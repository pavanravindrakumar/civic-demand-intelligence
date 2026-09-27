import pytest
from backend.app.analytics.engine import (
    CivicAnalyticsEngine, PriorityWeights, VillageInput,
    ReadinessState, EvidenceQuality
)

@pytest.fixture
def engine():
    weights = PriorityWeights(
        infrastructure_gap=0.5,
        validated_demand=0.3,
        household_exposure=0.2
    )
    return CivicAnalyticsEngine(weights)

def test_zero_gap(engine):
    inp = VillageInput(
        lgd_village_code="101",
        households=100,
        fhtc_house_connections=100,
        reported_household_gap=0,
        validated_citizen_demand_count=10
    )
    res = engine.assess_village(inp)
    assert res.readiness == ReadinessState.READY
    assert res.normalized_gap == 0.0
    assert res.reported_household_gap == 0
    assert res.priority_score is not None

def test_positive_gap(engine):
    inp = VillageInput(
        lgd_village_code="102",
        households=100,
        fhtc_house_connections=50,
        reported_household_gap=50,
        validated_citizen_demand_count=10
    )
    res = engine.assess_village(inp)
    assert res.readiness == ReadinessState.READY
    assert res.normalized_gap == 0.5

def test_households_equals_fhtc(engine):
    inp = VillageInput(
        lgd_village_code="103",
        households=50,
        fhtc_house_connections=50,
        reported_household_gap=0,
        validated_citizen_demand_count=5
    )
    res = engine.assess_village(inp)
    assert res.readiness == ReadinessState.READY
    assert res.normalized_gap == 0.0

def test_invalid_fhtc_gt_households(engine):
    inp = VillageInput(
        lgd_village_code="104",
        households=50,
        fhtc_house_connections=100,
        reported_household_gap=0
    )
    res = engine.assess_village(inp)
    assert res.readiness == ReadinessState.INVALID_INPUTS
    assert res.priority_score is None

def test_negative_values(engine):
    inp = VillageInput(
        lgd_village_code="105",
        households=-10,
        fhtc_house_connections=0,
        reported_household_gap=0
    )
    res = engine.assess_village(inp)
    assert res.readiness == ReadinessState.INVALID_INPUTS

def test_normalization_lower_bound(engine):
    inp = VillageInput(
        lgd_village_code="106",
        households=0,
        fhtc_house_connections=0,
        reported_household_gap=0,
        validated_citizen_demand_count=0
    )
    res = engine.assess_village(inp)
    assert res.normalized_gap == 0.0
    assert res.normalized_demand == 0.0
    assert res.normalized_exposure == 0.0

def test_normalization_upper_bound_and_saturation(engine):
    inp = VillageInput(
        lgd_village_code="107",
        households=5000,
        fhtc_house_connections=0,
        reported_household_gap=5000,
        validated_citizen_demand_count=1000
    )
    res = engine.assess_village(inp)
    assert res.normalized_gap == 1.0
    assert res.normalized_exposure == 1.0
    assert res.normalized_demand == 1.0

def test_missing_demand(engine):
    inp = VillageInput(
        lgd_village_code="108",
        households=100,
        fhtc_house_connections=50,
        reported_household_gap=50,
        validated_citizen_demand_count=None
    )
    res = engine.assess_village(inp)
    assert res.readiness == ReadinessState.PUBLIC_EVIDENCE_ONLY
    assert res.evidence_quality == EvidenceQuality.PARTIAL
    assert res.priority_score is None
    assert res.normalized_demand == 0.0

def test_complete_priority_inputs_and_repeatability(engine):
    inp = VillageInput(
        lgd_village_code="109",
        households=1000,
        fhtc_house_connections=0,
        reported_household_gap=1000,
        validated_citizen_demand_count=50
    )
    res1 = engine.assess_village(inp)
    res2 = engine.assess_village(inp)

    assert res1.readiness == ReadinessState.READY
    # Weight calculation: gap(1.0)*0.5 + exposure(1.0)*0.2 + demand(1.0)*0.3 = 1.0
    assert res1.priority_score == 1.0
    assert res1.priority_score == res2.priority_score

def test_factor_contribution_sum(engine):
    inp = VillageInput(
        lgd_village_code="110",
        households=500,
        fhtc_house_connections=250,
        reported_household_gap=250,
        validated_citizen_demand_count=25
    )
    res = engine.assess_village(inp)
    # gap=0.5, exposure=0.5, demand=0.5
    # score = 0.5*0.5 + 0.5*0.2 + 0.5*0.3 = 0.5
    assert res.priority_score == 0.5

def test_invalid_weights():
    # Weights should normally be validated, but currently we just instantiate
    # If the user provides weights that don't sum to 1.0, the calculation is deterministic but could exceed 1.0
    # Engine logic bounds it via min(1.0, score)
    engine_bad = CivicAnalyticsEngine(PriorityWeights(
        infrastructure_gap=1.0,
        validated_demand=1.0,
        household_exposure=1.0
    ))
    inp = VillageInput(
        lgd_village_code="111",
        households=1000,
        fhtc_house_connections=0,
        reported_household_gap=1000,
        validated_citizen_demand_count=50
    )
    res = engine_bad.assess_village(inp)
    assert res.priority_score == 1.0 # Capped

def test_calculation_version_propagation(engine):
    inp = VillageInput(
        lgd_village_code="112",
        households=10,
        fhtc_house_connections=1,
        reported_household_gap=9
    )
    res = engine.assess_village(inp)
    assert res.calculation_version == "v1.0"
