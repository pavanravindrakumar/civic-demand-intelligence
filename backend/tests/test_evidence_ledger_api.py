import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid
import json
import os
import tempfile

from backend.app.main import app
from backend.app.models.evidence_ledger import EvidenceLedgerEntry
from backend.app.data.evidence_ledger_repository import evidence_ledger_repository

client = TestClient(app)

def create_mock_entry(lgd_code, need_type, timestamp, prio_version="v1", score=0.5):
    entry = EvidenceLedgerEntry(
        ledger_entry_id=str(uuid.uuid4()),
        priority_assessment_id=str(uuid.uuid4()),
        convergence_opportunity_id=str(uuid.uuid4()),
        unmet_demand_assessment_id=str(uuid.uuid4()),
        lgd_village_code=lgd_code,
        canonical_need_type=need_type,
        sector="WATER" if "WATER" in need_type else "ROADS",
        priority_score=score,
        factor_inputs_normalized={"gap": 0.5},
        factor_contributions={"gap": 0.25},
        priority_version=prio_version,
        calculation_version="v1",
        reported_household_gap=50,
        signal_count=10,
        generated_at=timestamp,
        record_hash=""
    )
    entry.record_hash = entry.calculate_hash()
    return entry

@pytest.fixture(autouse=True)
def setup_teardown():
    now = datetime.now(timezone.utc)

    entries = [
        create_mock_entry("111111", "WATER_SUPPLY_DEFICIT", now),
        create_mock_entry("222222", "ROAD_CONNECTIVITY_DEFICIT", now, prio_version="v2"),
        create_mock_entry("111111", "WATER_QUALITY_ISSUE", now, score=0.9),
    ]

    original_dir = evidence_ledger_repository.storage_dir
    original_file = evidence_ledger_repository.file_path
    original_cache = evidence_ledger_repository._cache

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_ledger_repository.storage_dir = tmpdir
        evidence_ledger_repository.file_path = os.path.join(tmpdir, "evidence_ledger.jsonl")
        evidence_ledger_repository._cache = None

        with open(evidence_ledger_repository.file_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(entry.model_dump_json() + "\n")

        yield

        evidence_ledger_repository.storage_dir = original_dir
        evidence_ledger_repository.file_path = original_file
        evidence_ledger_repository._cache = original_cache

def test_get_collection():
    response = client.get("/api/evidence/ledger")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Verify no PII
    assert "submitter_pseudonym" not in data[0]

def test_filter_by_village():
    response = client.get("/api/evidence/ledger?lgd_village_code=111111")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for item in data:
        assert item["lgd_village_code"] == "111111"

def test_filter_by_need():
    response = client.get("/api/evidence/ledger?canonical_need_type=ROAD_CONNECTIVITY_DEFICIT")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["canonical_need_type"] == "ROAD_CONNECTIVITY_DEFICIT"

def test_filter_by_priority_version():
    response = client.get("/api/evidence/ledger?priority_version=v2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["priority_version"] == "v2"

def test_detail_endpoint():
    # First get an assessment ID
    all_data = client.get("/api/evidence/ledger").json()
    target_id = all_data[0]["priority_assessment_id"]

    response = client.get(f"/api/evidence/ledger/{target_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["priority_assessment_id"] == target_id
    assert "factor_contributions" in data[0]
    assert data[0]["factor_contributions"]["gap"] == 0.25

def test_not_found():
    response = client.get("/api/evidence/ledger/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_limit_enforcement():
    response = client.get("/api/evidence/ledger?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

def test_invalid_limit():
    response = client.get("/api/evidence/ledger?limit=500")
    assert response.status_code == 422 # Max 100

def test_invalid_village_code():
    response = client.get("/api/evidence/ledger?lgd_village_code=abc")
    assert response.status_code == 422
