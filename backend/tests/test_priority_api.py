import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid
import json

from backend.app.main import app
from backend.app.models.priority_assessment import PriorityAssessment
from backend.app.data.priority_assessment_repository import priority_assessment_repository

client = TestClient(app)

@pytest.fixture
def mock_assessments(monkeypatch):
    assessments = [
        PriorityAssessment(
            assessment_id="a1",
            opportunity_id="o1",
            lgd_village_code="111111",
            canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER",
            priority_score=0.8,
            priority_version="1.0.0-final",
            eligibility_status="CONVERGENCE_IDENTIFIED",
            factor_contributions={
                "gap_contribution": 0.4,
                "exposure_contribution": 0.1,
                "demand_contribution": 0.3
            },
            factor_inputs_normalized={
                "normalized_gap": 0.8,
                "normalized_exposure": 0.5,
                "normalized_demand": 1.0
            },
            evaluated_at=datetime.now(timezone.utc)
        ),
        PriorityAssessment(
            assessment_id="a2",
            opportunity_id="o2",
            lgd_village_code="222222",
            canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER",
            priority_score=0.9, # Higher score
            priority_version="1.0.0-final",
            eligibility_status="CONVERGENCE_IDENTIFIED",
            factor_contributions={
                "gap_contribution": 0.5,
                "exposure_contribution": 0.2,
                "demand_contribution": 0.2
            },
            factor_inputs_normalized={
                "normalized_gap": 1.0,
                "normalized_exposure": 1.0,
                "normalized_demand": 0.66
            },
            evaluated_at=datetime.now(timezone.utc)
        ),
        PriorityAssessment(
            assessment_id="a3",
            opportunity_id="o3",
            lgd_village_code="333333",
            canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER",
            priority_score=None, # No score
            priority_version="1.0.0-final",
            eligibility_status="PUBLIC_EVIDENCE_ONLY",
            factor_contributions={},
            factor_inputs_normalized={},
            evaluated_at=datetime.now(timezone.utc)
        )
    ]
    monkeypatch.setattr(priority_assessment_repository, "load_all", lambda: assessments)
    return assessments

def test_priority_collection(mock_assessments):
    response = client.get("/api/priority/assessments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Deterministic ordering: highest score first, then newest
    # a2 (0.9) > a1 (0.8) > a3 (None -> -1.0)
    assert data[0]["priority_assessment_id"] == "a2"
    assert data[1]["priority_assessment_id"] == "a1"
    assert data[2]["priority_assessment_id"] == "a3"

def test_filtering(mock_assessments):
    res_lgd = client.get("/api/priority/assessments?lgd_village_code=111111")
    assert len(res_lgd.json()) == 1

    res_need = client.get("/api/priority/assessments?canonical_need_type=WATER_SUPPLY_DEFICIT")
    assert len(res_need.json()) == 3

    res_sector = client.get("/api/priority/assessments?sector=WATER")
    assert len(res_sector.json()) == 3

    res_version = client.get("/api/priority/assessments?priority_version=2.0.0")
    assert len(res_version.json()) == 0

    res_status = client.get("/api/priority/assessments?eligibility_status=PUBLIC_EVIDENCE_ONLY")
    assert len(res_status.json()) == 1

def test_invalid_lgd():
    res = client.get("/api/priority/assessments?lgd_village_code=invalid")
    assert res.status_code == 422 # FastAPI validation

def test_priority_detail(mock_assessments):
    response = client.get("/api/priority/assessments/a1")
    assert response.status_code == 200
    data = response.json()

    # exact factor preservation
    assert data["priority_score"] == 0.8
    assert data["priority_version"] == "1.0.0-final"
    assert data["calculation_version"] == "v1.0"

    factors = data["factors"]
    assert "infrastructure_gap" in factors
    assert factors["infrastructure_gap"]["normalized_input"] == 0.8
    assert factors["infrastructure_gap"]["contribution"] == 0.4

    # Prove no PII leakage in schema
    assert "submitter" not in data
    assert "raw_text" not in data
    assert "pseudonym" not in data

    # Provenance tags
    assert data["citizen_evidence_provenance"] == "SYNTHETIC_DEMO_SIGNAL"
    assert data["public_evidence_provenance"] == "REAL_JJM_LGD"
    assert "population" not in data

def test_no_score_behavior(mock_assessments):
    response = client.get("/api/priority/assessments/a3")
    assert response.status_code == 200
    data = response.json()

    assert data["priority_score"] is None
    assert data["eligibility_status"] == "PUBLIC_EVIDENCE_ONLY"
    assert data["factors"] == {} # No fabricated explanations

def test_nonexistent_assessment(mock_assessments):
    response = client.get("/api/priority/assessments/missing")
    assert response.status_code == 404
