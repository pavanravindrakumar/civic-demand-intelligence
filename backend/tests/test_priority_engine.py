import pytest
from datetime import datetime, timezone
import uuid

from backend.app.models.convergence_opportunity import ConvergenceOpportunity
from backend.app.data.convergence_repository import ConvergenceOpportunityRepository
from backend.app.data.priority_assessment_repository import PriorityAssessmentRepository
from backend.app.analytics.engine import PriorityWeights
from backend.app.analytics.priority_engine import ConvergencePriorityEngine

class MockConvergenceRepo(ConvergenceOpportunityRepository):
    def __init__(self):
        self._data = []

    def load_all(self):
        return self._data

    def add_opportunity(
        self,
        state="CONVERGENCE_IDENTIFIED",
        gap=50,
        exposure=100,
        signals=25
    ):
        self._data.append(ConvergenceOpportunity(
            opportunity_id=str(uuid.uuid4()),
            assessment_id=str(uuid.uuid4()),
            lgd_village_code="111111",
            canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER",
            convergence_state=state,
            scheme_status="NOT_AVAILABLE",
            reported_household_gap=gap,
            household_exposure=exposure,
            signal_count=signals,
            distinct_submitter_count=signals,
            public_evidence_vintage=datetime.now(timezone.utc),
            demand_aggregation_window_start=datetime.now(timezone.utc),
            demand_aggregation_window_end=datetime.now(timezone.utc),
            evaluated_at=datetime.now(timezone.utc),
            calculation_version="v1"
        ))

class MockPriorityRepo(PriorityAssessmentRepository):
    def __init__(self):
        self.saved = []
    def overwrite_assessments(self, assessments):
        self.saved = assessments

@pytest.fixture
def engine():
    conv_repo = MockConvergenceRepo()
    prio_repo = MockPriorityRepo()
    weights = PriorityWeights(
        version="priority-v1",
        infrastructure_gap=0.5,
        validated_demand=0.3,
        household_exposure=0.2
    )
    return ConvergencePriorityEngine(weights, conv_repo, prio_repo), conv_repo, prio_repo

def test_priority_calculation_deterministic(engine):
    eng, conv, prio = engine
    conv.add_opportunity(state="CONVERGENCE_IDENTIFIED", gap=50, exposure=100, signals=25)

    # Gap: 50/100 = 0.5 * 0.5 = 0.25
    # Exposure: 100/1000 = 0.1 * 0.2 = 0.02
    # Demand: 25/50 = 0.5 * 0.3 = 0.15
    # Total Score = 0.42

    results = eng.calculate_priorities()
    assert len(results) == 1
    res = results[0]

    assert pytest.approx(res.priority_score) == 0.42
    assert res.factor_inputs_normalized["normalized_gap"] == 0.5
    assert res.factor_inputs_normalized["normalized_exposure"] == 0.1
    assert res.factor_inputs_normalized["normalized_demand"] == 0.5

    assert pytest.approx(res.factor_contributions["gap_contribution"]) == 0.25
    assert pytest.approx(res.factor_contributions["exposure_contribution"]) == 0.02
    assert pytest.approx(res.factor_contributions["demand_contribution"]) == 0.15

def test_eligibility_rules(engine):
    eng, conv, prio = engine
    # Only CONVERGENCE_IDENTIFIED gets scored
    conv.add_opportunity(state="PUBLIC_EVIDENCE_ONLY")
    conv.add_opportunity(state="DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE")
    conv.add_opportunity(state="INCOMPLETE_CONVERGENCE")

    results = eng.calculate_priorities()
    assert len(results) == 3
    for r in results:
        assert r.priority_score is None
        assert r.eligibility_status != "CONVERGENCE_IDENTIFIED"

def test_bounding_and_saturation(engine):
    eng, conv, prio = engine
    # Extreme numbers shouldn't break the [0,1] bound
    conv.add_opportunity(state="CONVERGENCE_IDENTIFIED", gap=150, exposure=100, signals=1000)

    # Gap: max(1.0, 150/100) -> 1.0 * 0.5 = 0.5
    # Exposure: 100/1000 -> 0.1 * 0.2 = 0.02
    # Demand: max(1.0, 1000/50) -> 1.0 * 0.3 = 0.3
    # Total Score = 0.82

    results = eng.calculate_priorities()
    assert len(results) == 1
    res = results[0]

    assert pytest.approx(res.priority_score) == 0.82
    assert res.factor_inputs_normalized["normalized_demand"] == 1.0
    assert pytest.approx(res.factor_contributions["demand_contribution"]) == 0.3

def test_rebuildability(engine):
    eng, conv, prio = engine
    conv.add_opportunity(state="CONVERGENCE_IDENTIFIED")

    eng.calculate_priorities()
    assert len(prio.saved) == 1

    # Identical overwrite
    eng.calculate_priorities()
    assert len(prio.saved) == 1

def test_missing_inputs_and_zero_division(engine):
    eng, conv, prio = engine
    # Missing gap and exposure, households=0
    conv.add_opportunity(state="CONVERGENCE_IDENTIFIED", gap=None, exposure=0, signals=None)

    results = eng.calculate_priorities()
    assert len(results) == 1
    res = results[0]

    # Gap defaults to 0, households is 0, so division by zero avoided = 0.0
    # Exposure is 0 / 1000 = 0.0
    # Signals default to 0 / 50 = 0.0
    assert pytest.approx(res.priority_score) == 0.0
    assert res.factor_inputs_normalized["normalized_gap"] == 0.0
    assert res.factor_inputs_normalized["normalized_exposure"] == 0.0
    assert res.factor_inputs_normalized["normalized_demand"] == 0.0
