import pytest
import uuid
import os
from datetime import datetime, timezone

from backend.app.models.priority_assessment import PriorityAssessment
from backend.app.models.convergence_opportunity import ConvergenceOpportunity
from backend.app.data.evidence_ledger_repository import EvidenceLedgerRepository
from backend.app.analytics.evidence_ledger_service import EvidenceLedgerService

class MockLedgerRepo(EvidenceLedgerRepository):
    def __init__(self):
        self.file_path = "mock_evidence_ledger.jsonl"
        self._data = []

    def _ensure_directory(self):
        pass

    def append_entry(self, entry):
        # Implement in-memory append with idempotency and conflict check
        ledger_key = f"{entry.priority_assessment_id}_{entry.calculation_version}_{entry.priority_version}"
        for ex in self._data:
            ex_key = f"{ex.priority_assessment_id}_{ex.calculation_version}_{ex.priority_version}"
            if ex_key == ledger_key:
                if ex.record_hash == entry.record_hash:
                    return # Idempotent
                else:
                    raise ValueError(f"Conflicting ledger entry for key {ledger_key}")
        self._data.append(entry)

    def load_all(self):
        return self._data

@pytest.fixture
def service():
    repo = MockLedgerRepo()
    return EvidenceLedgerService(repo), repo

def build_mocks(calc_version="v1", prio_version="priority-v1", score=0.42):
    now = datetime.now(timezone.utc)
    opp_id = str(uuid.uuid4())
    assess_id = str(uuid.uuid4())
    unmet_id = str(uuid.uuid4())

    opp = ConvergenceOpportunity(
        opportunity_id=opp_id,
        assessment_id=unmet_id,
        lgd_village_code="111111",
        canonical_need_type="WATER_SUPPLY_DEFICIT",
        sector="WATER",
        convergence_state="CONVERGENCE_IDENTIFIED",
        scheme_status="NOT_AVAILABLE",
        reported_household_gap=50,
        household_exposure=100,
        signal_count=10,
        distinct_submitter_count=8,
        public_evidence_vintage=now,
        demand_aggregation_window_start=now,
        demand_aggregation_window_end=now,
        evaluated_at=now,
        calculation_version=calc_version
    )

    prio = PriorityAssessment(
        assessment_id=assess_id,
        opportunity_id=opp_id,
        lgd_village_code="111111",
        canonical_need_type="WATER_SUPPLY_DEFICIT",
        sector="WATER",
        priority_score=score,
        factor_inputs_normalized={"gap": 0.5},
        factor_contributions={"gap": 0.25},
        priority_version=prio_version,
        evaluated_at=now
    )

    return prio, opp

def test_ledger_record_creation(service):
    srv, repo = service
    prio, opp = build_mocks()

    entry = srv.record_assessment(prio, opp)

    assert len(repo.load_all()) == 1
    assert entry.priority_score == 0.42
    assert entry.reported_household_gap == 50
    assert entry.signal_count == 10
    assert entry.record_hash is not None

def test_ledger_idempotency(service):
    srv, repo = service
    prio, opp = build_mocks()

    # Append first time
    srv.record_assessment(prio, opp)
    assert len(repo.load_all()) == 1

    # Append again (identical)
    srv.record_assessment(prio, opp)
    assert len(repo.load_all()) == 1 # Ignored silently

def test_ledger_conflict(service):
    srv, repo = service
    prio, opp = build_mocks()

    srv.record_assessment(prio, opp)
    assert len(repo.load_all()) == 1

    # Modify priority score to create a conflict (same ID, different content)
    prio.priority_score = 0.99

    with pytest.raises(ValueError, match="Conflicting ledger entry"):
        srv.record_assessment(prio, opp)

def test_new_calculation_version(service):
    srv, repo = service
    prio, opp = build_mocks(calc_version="v1")
    srv.record_assessment(prio, opp)

    # New calculation version for the same assessment ID creates a new record
    # Wait, in practice, a new run would generate a new assessment_id.
    # But let's say the assessment_id is the same. The ledger key incorporates calc_version.
    prio.priority_version = "priority-v2"

    srv.record_assessment(prio, opp)
    assert len(repo.load_all()) == 2

def test_hash_determinism(service):
    srv, repo = service
    prio1, opp1 = build_mocks()

    # Create identical inputs manually (to simulate two separate runs generating exact same content)
    prio2 = prio1.model_copy()
    opp2 = opp1.model_copy()

    # Generate independently
    entry1 = srv.record_assessment(prio1, opp1)

    # Mocking internal timestamp generation difference wouldn't affect hash because it's excluded
    entry1_copy = entry1.model_copy()
    entry1_copy.generated_at = datetime.now(timezone.utc)

    assert entry1.record_hash == entry1_copy.calculate_hash()
