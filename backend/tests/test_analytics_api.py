from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.analytics import get_analytics_repository
from backend.app.data.analytics_repository import AnalyticsRepository, AnalyticsSummary
from backend.app.analytics.engine import PriorityResult, ReadinessState, EvidenceQuality
import pytest

# Create a mock repository for tests to avoid hitting the real CSV
class MockAnalyticsRepository(AnalyticsRepository):
    def __init__(self):
        super().__init__(csv_path="dummy.csv")
        # Pre-populate some mock data
        self._summary = AnalyticsSummary(
            total_villages_analyzed=2,
            total_households=2000,
            total_fhtc=1000,
            total_reported_household_gap=1000,
            readiness_state=ReadinessState.PUBLIC_EVIDENCE_ONLY,
            calculation_version="v1.0",
            data_source="MOCK"
        )
        self._data = {
            "271010": PriorityResult(
                lgd_village_code="271010",
                readiness=ReadinessState.PUBLIC_EVIDENCE_ONLY,
                evidence_quality=EvidenceQuality.PARTIAL,
                calculation_version="v1.0",
                normalized_gap=0.5,
                normalized_exposure=1.0,
                normalized_demand=0.0,
                reported_household_gap=500,
                household_exposure=1000,
                priority_score=None
            )
        }
        self._loaded = True

@pytest.fixture
def override_repo():
    mock_repo = MockAnalyticsRepository()
    app.dependency_overrides[get_analytics_repository] = lambda: mock_repo
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client(override_repo):
    return TestClient(app)

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200

def test_summary_endpoint(client):
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_villages_analyzed"] == 2
    assert data["total_households"] == 2000
    assert data["total_reported_household_gap"] == 1000
    assert data["readiness_state"] == "PUBLIC_EVIDENCE_ONLY"
    assert data["data_source"] == "MOCK"

def test_village_lookup_endpoint(client):
    response = client.get("/api/analytics/village/271010")
    assert response.status_code == 200
    data = response.json()
    assert data["lgd_village_code"] == "271010"
    assert data["reported_household_gap"] == 500
    assert data["readiness"] == "PUBLIC_EVIDENCE_ONLY"
    assert data["priority_score"] is None

def test_unknown_village_lookup(client):
    response = client.get("/api/analytics/village/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
