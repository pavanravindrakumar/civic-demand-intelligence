import pytest
import os
import json
from backend.app.models.signal import StoredCitizenSignal
from backend.app.services.simulator_service import CivicSignalSimulator
from backend.app.data.synthetic_signal_repository import SyntheticSignalRepository
from backend.app.data.analytics_repository import AnalyticsRepository

class MockAnalyticsRepo(AnalyticsRepository):
    def __init__(self):
        super().__init__()
        # Mock load data
        from backend.app.analytics.engine import PriorityResult, ReadinessState, EvidenceQuality
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
        for s in self._data:
            if s.idempotency_key == idempotency_key:
                return s
        return None
    def store_signals(self, signals):
        self._data.extend(signals)
        return signals

@pytest.fixture
def simulator():
    repo_synth = MockSyntheticRepo()
    repo_ana = MockAnalyticsRepo()
    return CivicSignalSimulator(repo_synth, repo_ana), repo_synth

def test_water_convergence_scenario(simulator):
    sim, repo = simulator
    res = sim.generate_scenario("WATER_CONVERGENCE", "v1", "seed1", 5)

    assert res.target_lgd_village_code == "111111"
    assert res.generated_count == 5
    assert len(repo._data) == 5

    for s in repo._data:
        assert s.is_synthetic is True
        assert s.provenance == "SYNTHETIC_DEMO_SIGNAL"
        assert s.synthetic_scenario_id == "WATER_CONVERGENCE"
        assert s.lgd_village_code == "111111"
        assert s.source == "SIMULATOR"

def test_water_no_public_gap_scenario(simulator):
    sim, repo = simulator
    res = sim.generate_scenario("WATER_NO_PUBLIC_GAP", "v1", "seed1", 3)

    assert res.target_lgd_village_code == "222222"
    assert len(repo._data) == 3

def test_unresolved_geography_scenario(simulator):
    sim, repo = simulator
    res = sim.generate_scenario("UNRESOLVED_GEOGRAPHY", "v1", "seed1", 2)

    assert res.target_lgd_village_code is None
    assert repo._data[0].lgd_village_code is None

def test_non_water_demand(simulator):
    sim, repo = simulator
    res = sim.generate_scenario("NON_WATER_DEMAND", "v1", "seed1", 2)
    assert res.target_lgd_village_code == "111111"
    assert "road" in repo._data[0].raw_text.lower() or "health" in repo._data[0].raw_text.lower() or "రోడ్డు" in repo._data[0].raw_text.lower()

def test_determinism_and_idempotency(simulator):
    sim, repo = simulator
    sim.generate_scenario("WATER_CONVERGENCE", "v1", "seed1", 5)
    first_run_ids = [s.signal_id for s in repo._data]

    # Run again with same seed
    sim.generate_scenario("WATER_CONVERGENCE", "v1", "seed1", 5)
    assert len(repo._data) == 5 # no new records added

    # Check that IDs are identical (deterministic generation)
    assert first_run_ids == [s.signal_id for s in repo._data]

    # Run with different seed
    sim.generate_scenario("WATER_CONVERGENCE", "v1", "seed2", 5)
    assert len(repo._data) == 10

def test_multilingual_content(simulator):
    sim, repo = simulator
    sim.generate_scenario("WATER_CONVERGENCE", "v1", "seed1", 2)

    lang1 = repo._data[0].detected_language
    lang2 = repo._data[1].detected_language
    assert lang1 != lang2
    assert lang1 in ["en", "te"]
    assert lang2 in ["en", "te"]

def test_batch_limit_bounds(simulator):
    sim, repo = simulator
    res = sim.generate_scenario("WATER_CONVERGENCE", "v1", "seed1", 100)
    assert res.generated_count == 50 # max limit is 50
    assert len(repo._data) == 50
