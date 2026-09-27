import uuid
import hashlib
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.models.signal import StoredCitizenSignal
from backend.app.models.simulator import (
    ScenarioType,
    CivicSignalSimulationScenario,
    CivicSignalSimulationResult
)
from backend.app.data.synthetic_signal_repository import SyntheticSignalRepository
from backend.app.data.analytics_repository import AnalyticsRepository

class CivicSignalSimulator:
    """
    Deterministic simulator for generating synthetic Civic Signals.
    Ensures clear separation between real and synthetic data.
    """

    def __init__(self, synthetic_repo: SyntheticSignalRepository, analytics_repo: AnalyticsRepository):
        self.synthetic_repo = synthetic_repo
        self.analytics_repo = analytics_repo

    def _deterministic_uuid(self, seed: str, index: int) -> str:
        """Generate a deterministic UUID based on seed and index."""
        hash_bytes = hashlib.sha256(f"{seed}_{index}".encode('utf-8')).digest()
        return str(uuid.UUID(bytes=hash_bytes[:16]))

    def _select_target_village(self, condition_type: str) -> Optional[str]:
        # Force load data
        self.analytics_repo._load_data()

        # Sort keys for determinism
        lgd_codes = sorted(self.analytics_repo._data.keys())

        for lgd in lgd_codes:
            village_res = self.analytics_repo._data[lgd]
            gap = village_res.reported_household_gap

            if condition_type == "POSITIVE_GAP" and gap > 0:
                return lgd
            elif condition_type == "ZERO_GAP" and gap == 0:
                return lgd
            elif condition_type == "ANY":
                return lgd

        return None

    def _get_content_templates(self, scenario_id: ScenarioType, index: int) -> tuple[str, str]:
        """Returns deterministic (text, language) tuple based on scenario and index."""
        # Simple deterministic cycle
        if scenario_id == "WATER_CONVERGENCE" or scenario_id == "WATER_NO_PUBLIC_GAP" or scenario_id == "UNRESOLVED_GEOGRAPHY":
            templates = [
                ("గత రెండు వారాలుగా మాకు త్రాగునీరు రావడం లేదు.", "te"),
                ("We have not received any drinking water for the last two weeks.", "en"),
                ("పైపులైన్ పగిలిపోయి నెల రోజులు అవుతున్నా ఎవరూ పట్టించుకోలేదు.", "te"),
                ("The pipeline broke last month and it was never repaired.", "en"),
                ("Our village needs a proper tap connection, we walk 2km every day.", "en")
            ]
        elif scenario_id == "NON_WATER_DEMAND":
            templates = [
                ("The road to the main highway is completely washed away.", "en"),
                ("మా ఊరి రోడ్డు పూర్తిగా పాడైపోయింది, వాహనాలు వెళ్లలేవు.", "te"),
                ("We urgently need a primary health center here.", "en")
            ]
        else:
            templates = [("Default synthetic message.", "en")]

        tpl = templates[index % len(templates)]
        return tpl[0], tpl[1]

    def generate_scenario(
        self,
        scenario_id: ScenarioType,
        version: str,
        seed: str = "default_seed",
        batch_size: int = 10
    ) -> CivicSignalSimulationResult:
        """
        Generates deterministic synthetic signals for a given scenario.
        """
        # Bound limits
        batch_size = max(1, min(batch_size, 50))

        # Determine Geography
        target_lgd = None
        if scenario_id == "WATER_CONVERGENCE":
            target_lgd = self._select_target_village("POSITIVE_GAP")
        elif scenario_id == "WATER_NO_PUBLIC_GAP":
            target_lgd = self._select_target_village("ZERO_GAP")
        elif scenario_id == "NON_WATER_DEMAND":
            target_lgd = self._select_target_village("ANY")
        elif scenario_id == "UNRESOLVED_GEOGRAPHY":
            target_lgd = None

        generated_signals = []
        now = datetime.now(timezone.utc)

        for i in range(batch_size):
            signal_id = self._deterministic_uuid(f"{scenario_id}_{version}_{seed}", i)
            idempotency_key = f"{scenario_id}_{version}_{seed}_{i}"

            content, language = self._get_content_templates(scenario_id, i)

            # Check if idempotently generated already
            existing = self.synthetic_repo.check_idempotency(idempotency_key)
            if existing:
                generated_signals.append(existing)
                continue

            sig = StoredCitizenSignal(
                signal_id=signal_id,
                idempotency_key=idempotency_key,
                source="SIMULATOR",
                is_synthetic=True,
                provenance="SYNTHETIC_DEMO_SIGNAL",
                synthetic_scenario_id=scenario_id,
                raw_text=content,
                detected_language=language,
                extraction_status="PENDING",
                submitted_at=now,
                ingested_at=now,
                processing_version=version,
                lgd_village_code=target_lgd
            )

            generated_signals.append(sig)

        # Store newly generated
        new_signals = [s for s in generated_signals if s.extraction_status == "PENDING"] # simplistic filter
        # Better to just write them all via store_signals (in tests we might overwrite, but JSONL append is fine)
        # Actually idempotency check means we only get here if they are new.

        to_store = []
        for s in generated_signals:
            if not self.synthetic_repo.check_idempotency(s.idempotency_key):
                to_store.append(s)

        if to_store:
            self.synthetic_repo.store_signals(to_store)

        return CivicSignalSimulationResult(
            scenario_id=scenario_id,
            simulation_version=version,
            target_lgd_village_code=target_lgd,
            generated_count=batch_size
        )
