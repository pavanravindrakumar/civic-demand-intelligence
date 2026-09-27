import pytest
import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from backend.app.orchestrator.synthetic_pipeline import SyntheticCivicIntelligenceOrchestrator
from backend.app.services.simulator_service import CivicSignalSimulator
from backend.app.data.synthetic_signal_repository import SyntheticSignalRepository
from backend.app.data.analytics_repository import AnalyticsRepository
from backend.app.analytics.engine import PriorityResult, ReadinessState, EvidenceQuality, PriorityWeights
from backend.app.services.interpretation_service import CivicNeedInterpretationService
from backend.app.analytics.interpreter import SignalInterpreter, InterpretationError
from backend.app.data.civic_need_repository import CivicNeedRepository
from backend.app.models.civic_need import CivicNeed
from backend.app.analytics.demand_aggregator import CitizenDemandAggregator
from backend.app.data.demand_evidence_repository import CitizenDemandEvidenceRepository
from backend.app.analytics.unmet_demand_engine import UnmetDemandAssessmentEngine
from backend.app.data.unmet_demand_repository import UnmetDemandRepository
from backend.app.analytics.convergence_engine import ConvergenceOpportunityEngine
from backend.app.data.convergence_repository import ConvergenceOpportunityRepository
from backend.app.analytics.priority_engine import ConvergencePriorityEngine
from backend.app.data.priority_assessment_repository import PriorityAssessmentRepository
from backend.app.analytics.evidence_ledger_service import EvidenceLedgerService
from backend.app.data.evidence_ledger_repository import EvidenceLedgerRepository

# --- Mocks ---

class MockAnalyticsRepo(AnalyticsRepository):
    def __init__(self):
        super().__init__()
        self._data = {
            "111111": PriorityResult(
                lgd_village_code="111111", readiness=ReadinessState.READY, evidence_quality=EvidenceQuality.HIGH_CONFIDENCE,
                calculation_version="v1", normalized_gap=0.5, normalized_exposure=0.1, normalized_demand=0.5,
                reported_household_gap=50, household_exposure=100
            ),
            "222222": PriorityResult(
                lgd_village_code="222222", readiness=ReadinessState.READY, evidence_quality=EvidenceQuality.HIGH_CONFIDENCE,
                calculation_version="v1", normalized_gap=0.0, normalized_exposure=0.1, normalized_demand=0.5,
                reported_household_gap=0, household_exposure=100
            )
        }
    def _load_data(self):
        pass

class MockSyntheticRepo(SyntheticSignalRepository):
    def __init__(self):
        self._data = []
    def check_idempotency(self, idempotency_key):
        return next((s for s in self._data if s.idempotency_key == idempotency_key), None)
    def store_signals(self, signals):
        self._data.extend(signals)
        return signals
    def load_all(self):
        return self._data

class MockInterpreter(SignalInterpreter):
    def interpret(self, signal) -> CivicNeed:
        if "road" in signal.raw_text.lower() or "రోడ్డు" in signal.raw_text.lower():
            need = "ROAD_CONNECTIVITY_DEFICIT"
            sector = "ROADS"
        else:
            need = "WATER_SUPPLY_DEFICIT"
            sector = "WATER"
        return CivicNeed(
            need_id=f"need_{signal.signal_id}",
            source_signal_id=signal.signal_id,
            canonical_need_type=need,
            sector=sector,
            lgd_village_code=signal.lgd_village_code,
            detected_language=signal.detected_language,
            first_seen_at=signal.submitted_at,
            source_channel=signal.source,
            processing_version="mock-v1",
            need_label_en="Mock Need",
            location_expression="Mock Location",
            location_confidence=0.9,
            urgency="MEDIUM",
            last_updated_at=signal.submitted_at
        )

class MockCivicNeedRepo(CivicNeedRepository):
    def __init__(self):
        self._data = []
    def store_civic_need(self, need):
        self._data.append(need)
        return need
    def get_by_source_signal_id(self, sid):
        return next((n for n in self._data if n.source_signal_id == sid), None)
    def load_all(self):
        return self._data

class MockDemandEvidenceRepo(CitizenDemandEvidenceRepository):
    def __init__(self):
        self._data = []
    def overwrite_evidence(self, items):
        self._data = items
    def load_all(self):
        return self._data

class MockUnmetDemandRepo(UnmetDemandRepository):
    def __init__(self):
        self._data = []
    def overwrite_assessments(self, items):
        self._data = items
    def load_all(self):
        return self._data

class MockConvergenceRepo(ConvergenceOpportunityRepository):
    def __init__(self):
        self._data = []
    def overwrite_opportunities(self, items):
        self._data = items
    def load_all(self):
        return self._data

class MockPriorityAssessmentRepo(PriorityAssessmentRepository):
    def __init__(self):
        self._data = []
    def overwrite_assessments(self, items):
        self._data = items
    def load_all(self):
        return self._data

class MockEvidenceLedgerRepo(EvidenceLedgerRepository):
    def __init__(self):
        self._data = []
    def _ensure_directory(self):
        pass
    def append_entry(self, entry):
        self._data.append(entry)
    def load_all(self):
        return self._data

@pytest.fixture
def orchestrator():
    synth_repo = MockSyntheticRepo()
    ana_repo = MockAnalyticsRepo()
    simulator = CivicSignalSimulator(synth_repo, ana_repo)

    interpreter = MockInterpreter()
    need_repo = MockCivicNeedRepo()
    interp_service = CivicNeedInterpretationService(interpreter, need_repo)

    demand_repo = MockDemandEvidenceRepo()
    aggregator = CitizenDemandAggregator(demand_repo)

    unmet_repo = MockUnmetDemandRepo()
    unmet_engine = UnmetDemandAssessmentEngine(ana_repo, demand_repo, unmet_repo)

    conv_repo = MockConvergenceRepo()
    conv_engine = ConvergenceOpportunityEngine(unmet_repo, conv_repo)

    prio_repo = MockPriorityAssessmentRepo()
    weights = PriorityWeights()
    prio_engine = ConvergencePriorityEngine(weights, conv_repo, prio_repo)

    ledger_repo = MockEvidenceLedgerRepo()
    ledger_service = EvidenceLedgerService(ledger_repo)

    orch = SyntheticCivicIntelligenceOrchestrator(
        simulator, interp_service, aggregator, unmet_engine, conv_engine, prio_engine, ledger_service
    )

    return orch, synth_repo, need_repo, demand_repo, unmet_repo, conv_repo, prio_repo, ledger_repo

def test_water_convergence_pipeline(orchestrator):
    orch, synth_repo, need_repo, demand_repo, unmet_repo, conv_repo, prio_repo, ledger_repo = orchestrator

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    end = now + timedelta(days=7)

    summary = orch.run_pipeline("WATER_CONVERGENCE", "v1", start, end, batch_size=5)

    if summary.pipeline_status == "FAILED":
        print(f"PIPELINE ERROR: {summary.error_stage}")
    assert summary.pipeline_status == "COMPLETED"
    assert summary.generated_signal_count == 5
    assert summary.interpreted_need_count == 5
    assert summary.demand_evidence_count == 1  # 5 signals grouped into 1 aggregate for 1 village
    assert summary.unmet_demand_assessment_count == 1 # Positive gap village + demand
    assert summary.convergence_opportunity_count == 1 # DEMAND_SUPPORTED + JJM scheme logic
    assert summary.priority_assessment_count == 1 # Scored because CONVERGENCE_IDENTIFIED
    assert summary.ledger_entry_count == 2 # 2 total opportunities in mock repo evaluated (1 scored, 1 unscored)

    # Assert Synthetic Provenance survived
    ledger_entries = ledger_repo.load_all()
    assert len(ledger_entries) == 2
    # Find the scored one
    le = next(e for e in ledger_entries if e.priority_score is not None)

    assert le.lgd_village_code == "111111"
    assert le.canonical_need_type == "WATER_SUPPLY_DEFICIT"
    assert le.signal_count == 5
    assert le.reported_household_gap == 50
    assert le.priority_score is not None

def test_zero_gap_pipeline(orchestrator):
    orch, synth_repo, need_repo, demand_repo, unmet_repo, conv_repo, prio_repo, ledger_repo = orchestrator

    now = datetime.now(timezone.utc)
    summary = orch.run_pipeline("WATER_NO_PUBLIC_GAP", "v1", now - timedelta(days=7), now + timedelta(days=7), batch_size=3)

    assert summary.pipeline_status == "COMPLETED"
    assert summary.generated_signal_count == 3

    # Village 222222 has gap = 0
    # In unmet demand, this results in DEMAND_SUPPORTED (because demand exists)
    # but reported_household_gap is 0.
    # Convergence engine will see gap=0 and output DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE
    # Priority engine skips scoring

    assert summary.convergence_opportunity_count == 0
    assert summary.priority_assessment_count == 0
    assert summary.ledger_entry_count == 2 # 2 total opportunities in mock repo evaluated (0 scored, 2 unscored)

    convs = conv_repo.load_all()
    # It might create an opportunity but it's not CONVERGENCE_IDENTIFIED
    target = [c for c in convs if c.lgd_village_code == "222222"]
    assert target[0].convergence_state == "INCOMPLETE_CONVERGENCE"

def test_non_water_demand_pipeline(orchestrator):
    orch, synth_repo, need_repo, demand_repo, unmet_repo, conv_repo, prio_repo, ledger_repo = orchestrator

    now = datetime.now(timezone.utc)
    summary = orch.run_pipeline("NON_WATER_DEMAND", "v1", now - timedelta(days=7), now + timedelta(days=7), batch_size=2)

    assert summary.pipeline_status == "COMPLETED"
    # Needs are created (e.g. ROAD_CONNECTIVITY_DEFICIT)
    # Demand evidence created
    # But JJM analytics only maps WATER_SUPPLY_DEFICIT to public evidence
    # So Unmet Demand -> PUBLIC_EVIDENCE_UNSUPPORTED or similar
    # Convergence -> DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE

    assert summary.convergence_opportunity_count == 0
    assert summary.priority_assessment_count == 0
