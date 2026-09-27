import os
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_key",
        "DEMO_LIVE_GEMINI_ENABLED": "true"
    }):
        yield

@pytest.fixture(autouse=True)
def mock_gemini():
    with patch("backend.app.api.copilot.get_copilot_service") as mock_copilot, \
         patch("backend.app.api.demo_api.get_live_demo_orchestrator") as mock_demo:

        # Make copilot return success
        service_instance = MagicMock()
        service_instance.orchestrator.orchestrate.return_value = [
            MagicMock(role="model", content=MagicMock(text="Mock response", function_calls=[]))
        ]
        mock_copilot.return_value = service_instance

        # Make demo return success
        demo_instance = MagicMock()
        summary = MagicMock(
            scenario_id="WATER_CONVERGENCE",
            simulation_version="test",
            pipeline_status="COMPLETED",
            interpreted_need_count=1,
            generated_signal_count=1,
            demand_evidence_count=1,
            unmet_demand_assessment_count=1,
            convergence_opportunity_count=1,
            priority_assessment_count=1,
            ledger_entry_count=1,
            citizen_evidence_provenance="TEST",
            public_evidence_provenance="TEST",
            targeted_lgd_village_code="271010"
        )
        demo_instance.run_pipeline.return_value = summary
        mock_demo.return_value = demo_instance

        yield

def test_security_headers_present():
    response = client.get("/api/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "strict-origin" in response.headers.get("Referrer-Policy", "")
    assert response.headers.get("Cache-Control") == "no-store"
    # Localhost without explicit env/proto shouldn't have HSTS
    assert "Strict-Transport-Security" not in response.headers

def test_hsts_header_when_required():
    response = client.get("/api/health", headers={"x-forwarded-proto": "https"})
    assert "max-age=31536000" in response.headers.get("Strict-Transport-Security", "")

def test_request_id_generated_and_returned():
    response = client.get("/api/health")
    req_id = response.headers.get("X-Request-ID")
    assert req_id is not None
    assert len(req_id) > 10

def test_request_id_preserved_when_valid():
    test_id = "test-id-123"
    response = client.get("/api/health", headers={"X-Request-ID": test_id})
    assert response.headers.get("X-Request-ID") == test_id

def test_request_id_sanitized_when_invalid():
    invalid_id = "bad ID @#!"
    response = client.get("/api/health", headers={"X-Request-ID": invalid_id})
    assert response.headers.get("X-Request-ID") != invalid_id
    assert len(response.headers.get("X-Request-ID")) > 10

def test_oversized_payload_rejected():
    # 100KB payload
    large_payload = {"message": "A" * (102400 + 10)}
    response = client.post("/api/copilot/chat", json=large_payload)
    assert response.status_code == 413
    assert "Payload Too Large" in response.json().get("detail", "")

def test_normal_payload_accepted():
    payload = {"message": "Hello"}
    response = client.post("/api/copilot/chat", json=payload, headers={"X-Forwarded-For": "normal.ip"})
    assert response.status_code == 200

def test_rate_limiting_copilot():
    from backend.app.api.middleware import copilot_limiter
    copilot_limiter._counts.clear()

    # Default is 5 requests per 60s
    test_ip = "192.168.1.100"
    for _ in range(5):
        response = client.post("/api/copilot/chat", json={"message": "Hello"}, headers={"X-Forwarded-For": test_ip})
        assert response.status_code == 200

    response = client.post("/api/copilot/chat", json={"message": "Hello"}, headers={"X-Forwarded-For": test_ip})
    assert response.status_code == 429
    assert "Retry-After" in response.headers

    # Another IP succeeds
    response_other = client.post("/api/copilot/chat", json={"message": "Hello"}, headers={"X-Forwarded-For": "192.168.1.200"})
    assert response_other.status_code == 200

def test_rate_limiting_demo():
    from backend.app.api.middleware import demo_limiter
    demo_limiter._counts.clear()

    # Default is 2 requests per 60s
    test_ip = "10.0.0.100"
    for _ in range(2):
        response = client.post("/api/demo/scenarios/live/water-convergence", headers={"X-Forwarded-For": test_ip})
        assert response.status_code == 200

    response = client.post("/api/demo/scenarios/live/water-convergence", headers={"X-Forwarded-For": test_ip})
    assert response.status_code == 429
    assert "Retry-After" in response.headers
