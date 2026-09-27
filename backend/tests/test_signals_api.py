import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.data.signal_repository import signal_repository
import os
import json

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_signal_data(tmp_path):
    # Redirect repository to use tmp_path
    old_dir = signal_repository.storage_dir
    old_path = signal_repository.file_path

    signal_repository.storage_dir = str(tmp_path)
    signal_repository.file_path = os.path.join(str(tmp_path), "test_signals.jsonl")
    signal_repository._ensure_directory()

    yield

    signal_repository.storage_dir = old_dir
    signal_repository.file_path = old_path

def test_submit_valid_text_signal():
    payload = {
        "source": "TEXT",
        "raw_content": "We need better drinking water in Addateegala.",
        "language_hint": "en",
        "is_synthetic": False
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "RECEIVED"
    assert "signal_id" in data
    assert data["is_synthetic"] is False
    assert "pending" in data["reference_message"]

def test_submit_simulator_signal():
    payload = {
        "source": "SIMULATOR",
        "raw_content": "Simulated lack of electricity.",
        "is_synthetic": True
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 201
    assert response.json()["is_synthetic"] is True

def test_submit_future_voice_representation():
    # Audio uploads would use a different multipart route, but a JSON proxy representing voice
    payload = {
        "source": "VOICE",
        "raw_content": "Transcript or placeholder for voice.",
        "is_synthetic": False
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 201

def test_submit_future_messaging_representation():
    # No PII like phone number is included
    payload = {
        "source": "MESSAGING",
        "raw_content": "WhatsApp message about roads",
        "is_synthetic": False
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 201

def test_submit_invalid_channel():
    payload = {
        "source": "TELEPATHY",
        "raw_content": "This should fail.",
        "is_synthetic": False
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 422 # Pydantic validation error

def test_submit_empty_content():
    payload = {
        "source": "TEXT",
        "raw_content": "Hi", # less than min_length=5
        "is_synthetic": False
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 422

def test_submit_invalid_lgd_code():
    payload = {
        "source": "TEXT",
        "raw_content": "We need a hospital.",
        "lgd_village_code": "123" # Not 6 digits
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 422

def test_submit_valid_lgd_code():
    payload = {
        "source": "TEXT",
        "raw_content": "We need a hospital here.",
        "lgd_village_code": "586842"
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 201

def test_idempotency_duplicate_submission():
    payload = {
        "source": "TEXT",
        "raw_content": "This is exactly the same message sent twice.",
        "idempotency_key": "custom_key_123",
        "is_synthetic": False
    }

    # First submission
    resp1 = client.post("/api/citizen-signals", json=payload)
    assert resp1.status_code == 201
    id1 = resp1.json()["signal_id"]

    # Second submission
    resp2 = client.post("/api/citizen-signals", json=payload)
    assert resp2.status_code == 201
    id2 = resp2.json()["signal_id"]

    assert id1 == id2
    assert "Duplicate" in resp2.json()["reference_message"]

def test_pii_fields_not_exposed():
    payload = {
        "source": "TEXT",
        "raw_content": "Just making sure no PII leaks in the response."
    }
    response = client.post("/api/citizen-signals", json=payload)
    data = response.json()
    assert "submitter_pseudonym" not in data
    assert "phone" not in data
    assert "name" not in data

def test_persistence_failure_handling(monkeypatch):
    def mock_store(*args, **kwargs):
        raise Exception("Disk full")

    monkeypatch.setattr(signal_repository, "store_signal", mock_store)

    payload = {
        "source": "TEXT",
        "raw_content": "This will fail saving.",
        "idempotency_key": "unique_fail_key"
    }
    response = client.post("/api/citizen-signals", json=payload)
    assert response.status_code == 500
    assert "Failed to store signal" in response.json()["detail"]
