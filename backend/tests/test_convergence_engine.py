import pytest
from datetime import datetime, timezone
import uuid

from backend.app.models.unmet_demand import UnmetDemandAssessment
from backend.app.data.unmet_demand_repository import UnmetDemandRepository
from backend.app.data.convergence_repository import ConvergenceOpportunityRepository
from backend.app.analytics.convergence_engine import ConvergenceOpportunityEngine

class MockUnmetDemandRepo(UnmetDemandRepository):
    def __init__(self):
        self._data = []

    def load_all(self):
        return self._data

    def add_assessment(
        self,
        lgd_code="111111",
        need_type="WATER_SUPPLY_DEFICIT",
        state="DEMAND_SUPPORTED",
        gap=50,
        signals=10
    ):
        self._data.append(UnmetDemandAssessment(
            assessment_id=str(uuid.uuid4()),
            lgd_village_code=lgd_code,
            canonical_need_type=need_type,
            sector="WATER" if "WATER" in need_type else "ROADS",
            evidence_state=state,
            public_evidence_vintage=datetime.now(timezone.utc),
            reported_household_gap=gap,
            household_exposure=100,
            demand_aggregation_window_start=datetime.now(timezone.utc),
            demand_aggregation_window_end=datetime.now(timezone.utc),
            signal_count=signals,
            distinct_submitter_count=signals,
            assessment_date=datetime.now(timezone.utc),
            assessment_version="v1"
        ))

class MockConvergenceRepo(ConvergenceOpportunityRepository):
    def __init__(self):
        self.saved = []
    def overwrite_opportunities(self, opportunities):
        self.saved = opportunities

@pytest.fixture
def engine():
    unmet = MockUnmetDemandRepo()
    conv = MockConvergenceRepo()
    return ConvergenceOpportunityEngine(unmet, conv), unmet, conv

def test_convergence_identified_water_gap(engine):
    eng, unmet, conv = engine
    unmet.add_assessment(state="DEMAND_SUPPORTED", gap=50)

    results = eng.evaluate_opportunities()
    assert len(results) == 1
    assert results[0].convergence_state == "CONVERGENCE_IDENTIFIED"
    assert results[0].scheme_status == "NOT_AVAILABLE"

def test_incomplete_convergence_zero_gap(engine):
    eng, unmet, conv = engine
    # Zero gap but demand says yes -> incomplete convergence
    unmet.add_assessment(state="DEMAND_SUPPORTED", gap=0)

    results = eng.evaluate_opportunities()
    assert len(results) == 1
    assert results[0].convergence_state == "INCOMPLETE_CONVERGENCE"

def test_public_evidence_only(engine):
    eng, unmet, conv = engine
    unmet.add_assessment(state="PUBLIC_EVIDENCE_ONLY", signals=None)

    results = eng.evaluate_opportunities()
    assert len(results) == 1
    assert results[0].convergence_state == "PUBLIC_EVIDENCE_ONLY"
    assert results[0].signal_count is None

def test_demand_without_relevant_public_evidence(engine):
    eng, unmet, conv = engine
    unmet.add_assessment(state="NO_RELEVANT_PUBLIC_EVIDENCE", gap=None)

    results = eng.evaluate_opportunities()
    assert len(results) == 1
    assert results[0].convergence_state == "DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE"
    assert results[0].reported_household_gap is None

def test_rebuildability(engine):
    eng, unmet, conv = engine
    unmet.add_assessment(state="DEMAND_SUPPORTED", gap=50)

    eng.evaluate_opportunities()
    assert len(conv.saved) == 1

    eng.evaluate_opportunities()
    assert len(conv.saved) == 1 # Idempotent overwrite
