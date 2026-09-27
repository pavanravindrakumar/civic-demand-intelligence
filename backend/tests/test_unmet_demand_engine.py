import pytest
from datetime import datetime, timezone
import uuid

from backend.app.models.demand_evidence import CitizenDemandEvidence
from backend.app.analytics.engine import PriorityResult, ReadinessState, EvidenceQuality
from backend.app.analytics.unmet_demand_engine import UnmetDemandAssessmentEngine
from backend.app.data.unmet_demand_repository import UnmetDemandRepository

class MockAnalyticsRepo:
    def __init__(self):
        self._data = {}

    def _load_data(self):
        pass

    def add_village(self, lgd_code: str, gap: int, exposure: int):
        self._data[lgd_code] = PriorityResult(
            lgd_village_code=lgd_code,
            readiness=ReadinessState.READY,
            evidence_quality=EvidenceQuality.HIGH_CONFIDENCE,
            calculation_version="v1",
            normalized_gap=0.5,
            normalized_exposure=0.5,
            normalized_demand=0.0,
            reported_household_gap=gap,
            household_exposure=exposure,
            priority_score=None
        )

class MockDemandRepo:
    def __init__(self):
        self._data = []

    def load_all(self):
        return self._data

    def add_evidence(self, lgd_code, need_type="WATER_SUPPLY_DEFICIT", count=5):
        self._data.append(CitizenDemandEvidence(
            demand_id=str(uuid.uuid4()),
            canonical_need_type=need_type,
            sector="WATER" if "WATER" in need_type else "ROADS",
            lgd_village_code=lgd_code,
            aggregation_window_start=datetime.now(timezone.utc),
            aggregation_window_end=datetime.now(timezone.utc),
            signal_count=count,
            distinct_submitter_count=count,
            source_channels=["TEXT"],
            latest_signal_at=datetime.now(timezone.utc),
            contributing_signal_ids=[],
            aggregation_version="v1"
        ))

class MockUnmetRepo(UnmetDemandRepository):
    def __init__(self):
        self.saved = []
    def overwrite_assessments(self, assessments):
        self.saved = assessments

@pytest.fixture
def engine():
    pub_repo = MockAnalyticsRepo()
    dem_repo = MockDemandRepo()
    unmet_repo = MockUnmetRepo()
    return UnmetDemandAssessmentEngine(pub_repo, dem_repo, unmet_repo), pub_repo, dem_repo, unmet_repo

def test_water_demand_with_public_gap(engine):
    eng, pub, dem, unmet = engine
    pub.add_village("111111", gap=50, exposure=100)
    dem.add_evidence("111111", need_type="WATER_SUPPLY_DEFICIT", count=10)

    results = eng.run_assessment()
    assert len(results) == 1
    res = results[0]

    assert res.evidence_state == "DEMAND_SUPPORTED"
    assert res.canonical_need_type == "WATER_SUPPLY_DEFICIT"
    assert res.reported_household_gap == 50
    assert res.signal_count == 10

def test_water_demand_zero_public_gap(engine):
    eng, pub, dem, unmet = engine
    pub.add_village("222222", gap=0, exposure=100) # Public says no gap
    dem.add_evidence("222222", need_type="WATER_SUPPLY_DEFICIT", count=5)

    results = eng.run_assessment()
    assert len(results) == 1
    res = results[0]

    assert res.evidence_state == "DEMAND_SUPPORTED"
    assert res.reported_household_gap == 0
    assert res.signal_count == 5

def test_water_demand_missing_public_evidence(engine):
    eng, pub, dem, unmet = engine
    # No public evidence added
    dem.add_evidence("333333", need_type="WATER_SUPPLY_DEFICIT", count=2)

    results = eng.run_assessment()
    assert len(results) == 1
    res = results[0]

    assert res.evidence_state == "DEMAND_WITHOUT_MATCHING_PUBLIC_EVIDENCE"
    assert res.reported_household_gap is None
    assert res.signal_count == 2

def test_public_evidence_no_citizen_demand(engine):
    eng, pub, dem, unmet = engine
    pub.add_village("444444", gap=20, exposure=50)
    # No citizen demand added

    results = eng.run_assessment()
    assert len(results) == 1
    res = results[0]

    assert res.evidence_state == "PUBLIC_EVIDENCE_ONLY"
    assert res.canonical_need_type == "WATER_SUPPLY_DEFICIT"
    assert res.reported_household_gap == 20
    assert res.signal_count is None

def test_different_need_same_village(engine):
    eng, pub, dem, unmet = engine
    pub.add_village("555555", gap=10, exposure=50)
    dem.add_evidence("555555", need_type="ROAD_CONNECTIVITY_DEFICIT", count=3)

    results = eng.run_assessment()
    # We should get TWO assessments:
    # 1. PUBLIC_EVIDENCE_ONLY for WATER_SUPPLY_DEFICIT (since we have public evidence but no water demand)
    # 2. NO_RELEVANT_PUBLIC_EVIDENCE for ROAD_CONNECTIVITY_DEFICIT
    assert len(results) == 2

    water = next(r for r in results if r.canonical_need_type == "WATER_SUPPLY_DEFICIT")
    roads = next(r for r in results if r.canonical_need_type == "ROAD_CONNECTIVITY_DEFICIT")

    assert water.evidence_state == "PUBLIC_EVIDENCE_ONLY"
    assert roads.evidence_state == "NO_RELEVANT_PUBLIC_EVIDENCE"
    assert roads.reported_household_gap is None
    assert roads.signal_count == 3

def test_citizen_demand_unresolved_geography(engine):
    eng, pub, dem, unmet = engine
    dem.add_evidence(None, need_type="WATER_SUPPLY_DEFICIT", count=100)

    results = eng.run_assessment()
    # Engine ignores unresolved geography because it cannot be attached to a village
    assert len(results) == 0

def test_rebuild_determinism(engine):
    eng, pub, dem, unmet = engine
    pub.add_village("111111", gap=50, exposure=100)
    dem.add_evidence("111111", need_type="WATER_SUPPLY_DEFICIT", count=10)

    eng.run_assessment()
    assert len(unmet.saved) == 1
    first_id = unmet.saved[0].assessment_id

    # Run again
    eng.run_assessment()
    assert len(unmet.saved) == 1
    # IDs will be different as they are generated per run, but length is 1 meaning no duplication
    # The artifact is completely overwritten.
    assert unmet.saved[0].lgd_village_code == "111111"
