import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid

from backend.app.main import app
from backend.app.models.demand_evidence import CitizenDemandEvidence
from backend.app.data.demand_evidence_repository import demand_evidence_repository

client = TestClient(app)

def seed_repository():
    now = datetime.now(timezone.utc)
    aggregates = [
        CitizenDemandEvidence(
            demand_id=str(uuid.uuid4()),
            canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER",
            lgd_village_code="111111",
            aggregation_window_start=now,
            aggregation_window_end=now,
            signal_count=5,
            distinct_submitter_count=3,
            source_channels=["TEXT", "VOICE"],
            latest_signal_at=now,
            contributing_signal_ids=["a","b","c","d","e"],
            aggregation_version="demand-v1"
        ),
        CitizenDemandEvidence(
            demand_id=str(uuid.uuid4()),
            canonical_need_type="ROAD_CONNECTIVITY_DEFICIT",
            sector="ROADS",
            lgd_village_code="111111",
            aggregation_window_start=now,
            aggregation_window_end=now,
            signal_count=2,
            distinct_submitter_count=2,
            source_channels=["TEXT"],
            latest_signal_at=now,
            contributing_signal_ids=["f","g"],
            aggregation_version="demand-v1"
        ),
        CitizenDemandEvidence(
            demand_id=str(uuid.uuid4()),
            canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER",
            lgd_village_code=None, # UNRESOLVED
            aggregation_window_start=now,
            aggregation_window_end=now,
            signal_count=10,
            distinct_submitter_count=8,
            source_channels=["TEXT", "VOICE"],
            latest_signal_at=now,
            contributing_signal_ids=["h","i"],
            aggregation_version="demand-v1"
        )
    ]
    demand_evidence_repository.overwrite_evidence(aggregates)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    seed_repository()
    yield
    # Teardown
    demand_evidence_repository.overwrite_evidence([])

def test_get_all_evidence():
    response = client.get("/api/demand/evidence")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Check ordering: signal_count desc (10, 5, 2)
    assert data[0]["signal_count"] == 10
    assert data[1]["signal_count"] == 5
    assert data[2]["signal_count"] == 2

    # Check internal IDs are not exposed
    assert "contributing_signal_ids" not in data[0]

def test_filter_by_need_type():
    response = client.get("/api/demand/evidence?canonical_need_type=ROAD_CONNECTIVITY_DEFICIT")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["canonical_need_type"] == "ROAD_CONNECTIVITY_DEFICIT"

def test_filter_by_geography_status_resolved():
    response = client.get("/api/demand/evidence?geography_status=RESOLVED")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for item in data:
        assert item["lgd_village_code"] is not None

def test_filter_by_geography_status_unresolved():
    response = client.get("/api/demand/evidence?geography_status=UNRESOLVED")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["lgd_village_code"] is None

def test_filter_by_village_code():
    response = client.get("/api/demand/evidence?lgd_village_code=111111")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Ensure needs remain distinct
    needs = {item["canonical_need_type"] for item in data}
    assert "WATER_SUPPLY_DEFICIT" in needs
    assert "ROAD_CONNECTIVITY_DEFICIT" in needs

def test_village_detail_route():
    # Using path parameter route
    response = client.get("/api/demand/evidence/111111")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Check ordering inside village detail
    assert data[0]["signal_count"] == 5
    assert data[1]["signal_count"] == 2

def test_invalid_village_code():
    response = client.get("/api/demand/evidence/abc")
    assert response.status_code == 422 # Validation error for pattern r"^\d{6}$"

def test_empty_evidence_state():
    response = client.get("/api/demand/evidence/999999")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0 # Empty list, not 404, not hallucinated zeroes

def test_limit():
    response = client.get("/api/demand/evidence?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["signal_count"] == 10 # Returns highest first
