from fastapi.testclient import TestClient
from backend.app.main import app
import pytest

client = TestClient(app)

def test_demo_api_water_convergence():
    payload = {
        "scenario_id": "WATER_CONVERGENCE",
        "batch_size": 2
    }
    response = client.post("/api/demo/scenarios/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "WATER_CONVERGENCE"
    assert data["pipeline_status"] == "COMPLETED"
    assert data["ai_interpretation_mode"] == "DEMO / DETERMINISTIC MOCK"

    # We should have generated some signals based on batch_size
    assert data["generated_signal_count"] == 2

    assert "lgd_village_code" in data
    assert data["lgd_village_code"] is not None

    # Provenance tags must exist and be exact
    assert data["citizen_evidence_provenance"] == "SYNTHETIC_DEMO_SIGNAL"
    assert data["public_evidence_provenance"] == "REAL_JJM_LGD"

def test_demo_api_water_no_public_gap():
    payload = {
        "scenario_id": "WATER_NO_PUBLIC_GAP",
        "batch_size": 1
    }
    response = client.post("/api/demo/scenarios/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "WATER_NO_PUBLIC_GAP"
    assert data["pipeline_status"] == "COMPLETED"
    assert data["generated_signal_count"] == 1

def test_demo_api_non_water_demand():
    payload = {
        "scenario_id": "NON_WATER_DEMAND",
        "batch_size": 2
    }
    response = client.post("/api/demo/scenarios/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "NON_WATER_DEMAND"
    assert data["pipeline_status"] == "COMPLETED"
    assert data["generated_signal_count"] == 2

def test_demo_api_unresolved_geography():
    payload = {
        "scenario_id": "UNRESOLVED_GEOGRAPHY",
        "batch_size": 1
    }
    response = client.post("/api/demo/scenarios/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "UNRESOLVED_GEOGRAPHY"
    assert data["pipeline_status"] == "COMPLETED"

def test_demo_api_unknown_scenario_rejected():
    payload = {
        "scenario_id": "ARBITRARY_SCENARIO",
        "batch_size": 1
    }
    response = client.post("/api/demo/scenarios/run", json=payload)
    assert response.status_code == 422 # Pydantic validation failure because it's a Literal

def test_demo_api_batch_size_upper_bound():
    payload = {
        "scenario_id": "WATER_CONVERGENCE",
        "batch_size": 100 # Exceeds 50
    }
    response = client.post("/api/demo/scenarios/run", json=payload)
    assert response.status_code == 422
    assert "batch_size" in response.text

def test_demo_api_malformed_request_rejected():
    payload = {
        "unknown_field": "test"
    }
    response = client.post("/api/demo/scenarios/run", json=payload)
    assert response.status_code == 422
