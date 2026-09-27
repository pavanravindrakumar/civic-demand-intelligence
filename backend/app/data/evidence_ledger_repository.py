import os
import json
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
from typing import List, Optional
from backend.app.models.evidence_ledger import EvidenceLedgerEntry

class EvidenceLedgerRepository:
    """
    Append-only storage for the Evidence Ledger.
    """
    def __init__(self, storage_dir: str = "data/local_development"):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "evidence_ledger.jsonl")
        self._cache = None
        self._key_hash_map = None
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def append_entry(self, entry: EvidenceLedgerEntry):
        """
        Appends a new ledger entry.
        Enforces idempotency and conflict detection based on record_hash.
        """
        # Determine the key for idempotency: priority_assessment_id + calculation_version + priority_version
        ledger_key = f"{entry.priority_assessment_id}_{entry.calculation_version}_{entry.priority_version}"

        # Load all to populate cache and key_hash_map
        if self._cache is None:
            self.load_all()

        # O(1) duplicate check
        if ledger_key in self._key_hash_map:
            if self._key_hash_map[ledger_key] == entry.record_hash:
                return
            else:
                logger.warning("Conflicting ledger entry", extra={"safe_context": {"repository": self.__class__.__name__, "key": ledger_key}})
                raise ValueError(f"Conflicting ledger entry for key {ledger_key}")

        # Append
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")

            self._cache.append(entry)
            self._key_hash_map[ledger_key] = entry.record_hash
        except Exception as e:
            logger.error("Repository persistence failure", extra={"safe_context": {"repository": self.__class__.__name__, "error_type": type(e).__name__}})
            raise

    def load_all(self) -> List[EvidenceLedgerEntry]:
        if self._cache is not None:
            return self._cache

        if not os.path.exists(self.file_path):
            self._cache = []
            self._key_hash_map = {}
            return self._cache

        results = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    results.append(EvidenceLedgerEntry(**data))
                except Exception as e:
                    logger.warning("Malformed JSONL line skipped", extra={"safe_context": {"repository": self.__class__.__name__, "line_number": line_number}})
                    continue

        self._cache = results
        self._key_hash_map = {}
        for r in results:
            key = f"{r.priority_assessment_id}_{r.calculation_version}_{r.priority_version}"
            self._key_hash_map[key] = r.record_hash

        return results

    def get_by_priority_assessment_id(self, assessment_id: str) -> List[EvidenceLedgerEntry]:
        return [e for e in self.load_all() if e.priority_assessment_id == assessment_id]

evidence_ledger_repository = EvidenceLedgerRepository()
