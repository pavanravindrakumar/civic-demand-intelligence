import pytest
import os
import tempfile
import uuid
from datetime import datetime, timezone, timedelta

from backend.app.models.civic_need import CivicNeed
from backend.app.data.demand_evidence_repository import CitizenDemandEvidenceRepository
from backend.app.analytics.demand_aggregator import CitizenDemandAggregator

@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmpdirname:
        repo = CitizenDemandEvidenceRepository(storage_dir=tmpdirname)
        yield repo

@pytest.fixture
def aggregator(temp_repo):
    return CitizenDemandAggregator(repository=temp_repo)

def create_mock_need(
    need_type="WATER_SUPPLY_DEFICIT",
    sector="WATER",
    lgd_village_code="123456",
    source_signal_id=None,
    submitter_pseudonym=None,
    source_channel="TEXT",
    timestamp=None
):
    if source_signal_id is None:
        source_signal_id = str(uuid.uuid4())
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    return CivicNeed(
        need_id=str(uuid.uuid4()),
        source_signal_id=source_signal_id,
        source_channel=source_channel,
        submitter_pseudonym=submitter_pseudonym,
        canonical_need_type=need_type,
        sector=sector,
        need_label_en=need_type,
        location_expression="Village",
        location_confidence=0.9,
        lgd_village_code=lgd_village_code,
        detected_language="en",
        urgency="HIGH",
        first_seen_at=timestamp,
        last_updated_at=timestamp,
        processing_version="v1"
    )

def test_aggregation_single_need(aggregator, temp_repo):
    needs = [create_mock_need()]
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    results = aggregator.aggregate_evidence(needs, start, end)
    assert len(results) == 1
    assert results[0].signal_count == 1
    assert results[0].canonical_need_type == "WATER_SUPPLY_DEFICIT"
    assert results[0].lgd_village_code == "123456"
    assert results[0].aggregation_version == "demand-v1"

    # Check repository state
    loaded = temp_repo.load_all()
    assert len(loaded) == 1

def test_aggregation_multiple_needs_same_group(aggregator):
    needs = [
        create_mock_need(submitter_pseudonym="user1", source_channel="TEXT"),
        create_mock_need(submitter_pseudonym="user2", source_channel="VOICE"),
        create_mock_need(submitter_pseudonym="user1", source_channel="TEXT") # Same pseudonym
    ]
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    results = aggregator.aggregate_evidence(needs, start, end)
    assert len(results) == 1

    agg = results[0]
    assert agg.signal_count == 3
    assert agg.distinct_submitter_count == 2
    assert sorted(agg.source_channels) == ["TEXT", "VOICE"]

def test_aggregation_distinct_groups(aggregator):
    needs = [
        create_mock_need(need_type="WATER_SUPPLY_DEFICIT", lgd_village_code="111111"),
        create_mock_need(need_type="WATER_SUPPLY_DEFICIT", lgd_village_code="222222"),
        create_mock_need(need_type="ROAD_CONNECTIVITY_DEFICIT", lgd_village_code="111111"),
    ]
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    results = aggregator.aggregate_evidence(needs, start, end)
    assert len(results) == 3 # 3 distinct (need_type, village) pairs

def test_aggregation_deduplicates_source_signal(aggregator):
    # Two CivicNeed records claiming to be from the exact same source_signal_id
    # (e.g. if idempotency failed upstream) should only be counted once.
    duplicate_signal_id = "sig-duplicate-123"
    needs = [
        create_mock_need(source_signal_id=duplicate_signal_id),
        create_mock_need(source_signal_id=duplicate_signal_id)
    ]
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    results = aggregator.aggregate_evidence(needs, start, end)
    assert len(results) == 1
    assert results[0].signal_count == 1

def test_unresolved_geography_remains_unresolved(aggregator):
    needs = [create_mock_need(lgd_village_code=None)]
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    results = aggregator.aggregate_evidence(needs, start, end)
    assert len(results) == 1
    assert results[0].lgd_village_code is None # Unresolved remains unresolved

def test_time_window_exclusion(aggregator):
    now = datetime.now(timezone.utc)
    old_need = create_mock_need(timestamp=now - timedelta(days=10))
    recent_need = create_mock_need(timestamp=now)

    start = now - timedelta(days=2)
    end = now + timedelta(days=1)

    results = aggregator.aggregate_evidence([old_need, recent_need], start, end)
    assert len(results) == 1
    assert results[0].signal_count == 1 # Only the recent one was included

def test_rebuild_idempotency(aggregator, temp_repo):
    needs = [create_mock_need()]
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)

    aggregator.aggregate_evidence(needs, start, end)
    assert len(temp_repo.load_all()) == 1

    # Running it again entirely replaces the file, it shouldn't duplicate
    aggregator.aggregate_evidence(needs, start, end)
    assert len(temp_repo.load_all()) == 1
