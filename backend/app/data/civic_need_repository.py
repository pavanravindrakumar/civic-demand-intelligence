import os
import json
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
from typing import Optional
from backend.app.models.civic_need import CivicNeed

class CivicNeedRepository:
    """
    Local development persistence mechanism for Civic Needs.
    Appends to a JSONL file in the local development directory.
    """
    def __init__(self, storage_dir: str = "data/local_development"):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "civic_needs.jsonl")
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def get_by_source_signal_id(self, source_signal_id: str) -> Optional[CivicNeed]:
        """
        Checks if a CivicNeed generated from the given signal already exists.
        Returns the existing CivicNeed if found, otherwise None.
        """
        if not os.path.exists(self.file_path):
            return None

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("source_signal_id") == source_signal_id:
                        return CivicNeed(**data)
                except Exception as e:
                    logger.warning("Malformed JSONL line skipped", extra={"safe_context": {"repository": self.__class__.__name__, "line_number": line_number}})
                    continue
        return None

    def store_civic_need(self, need: CivicNeed) -> CivicNeed:
        """
        Appends the CivicNeed to the local JSONL file.
        """
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(need.model_dump_json() + "\n")
        except Exception as e:
            logger.error("Repository persistence failure", extra={"safe_context": {"repository": self.__class__.__name__, "error_type": type(e).__name__}})
            raise
        return need

civic_need_repository = CivicNeedRepository()
