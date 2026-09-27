import os
import json
import uuid
import tempfile
from unittest.mock import patch
from datetime import datetime, timezone

from backend.app.data.evidence_ledger_repository import EvidenceLedgerRepository
from backend.app.models.evidence_ledger import EvidenceLedgerEntry

def test_evidence_ledger_repository_caching_regression():
    """
    Regression test for O(N^2) issue in EvidenceLedgerRepository.
    Ensures that calling append_entry multiple times does not repeatedly read the
    file from disk by tracking the number of 'open' calls made by load_all.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = EvidenceLedgerRepository(storage_dir=tmpdir)

        now = datetime.now(timezone.utc)

        # We will mock the built-in open within the repository's module
        # to count how many times it is called to read the ledger file.
        with patch("backend.app.data.evidence_ledger_repository.open", side_effect=open) as mock_open:
            # Helper to create an entry
            def create_entry(vid, score):
                return EvidenceLedgerEntry(
                    ledger_entry_id=f"entry-{vid}",
                    priority_assessment_id=f"assess-{vid}",
                    convergence_opportunity_id=f"opp-{vid}",
                    unmet_demand_assessment_id=f"unmet-{vid}",
                    lgd_village_code=vid,
                    canonical_need_type="WATER_SUPPLY_DEFICIT",
                    sector="WATER",
                    priority_score=score,
                    factor_inputs_normalized={"gap": 0.5},
                    factor_contributions={"gap": 0.5},
                    priority_version="v1",
                    calculation_version="v1",
                    generated_at=now,
                    record_hash="mock-hash"
                )

            entry1 = create_entry("V123", 0.8)
            repo.append_entry(entry1)

            entry2 = create_entry("V456", 0.9)
            repo.append_entry(entry2)

            entry3 = create_entry("V789", 0.5)
            repo.append_entry(entry3)

            # Count the number of times the file was opened for READING.
            # When appending, we write (mode="a") or read (mode="r").
            # The O(N^2) issue caused load_all to run on every append,
            # meaning it would read the file N times.
            read_calls = [c for c in mock_open.call_args_list if c.args[1] == "r"]

            # With the cache, load_all should either be called once or read the file at most once
            # because subsequent reads use the cache.
            assert len(read_calls) <= 1, f"Expected at most 1 read, got {len(read_calls)}"

            # Check correctness
            all_entries = repo.load_all()
            assert len(all_entries) == 3
