import os
import json
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from backend.app.models.signal import StoredCitizenSignal

class SyntheticSignalRepository:
    """
    Persistence mechanism for Synthetic Citizen Signals.
    Appends to a JSONL file in the local development directory.
    Separate from the real SignalRepository to prevent cross-contamination.
    """
    def __init__(self, storage_dir: str = "data/local_development"):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "synthetic_citizen_signals.jsonl")
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def check_idempotency(self, idempotency_key: str) -> Optional[StoredCitizenSignal]:
        if not os.path.exists(self.file_path):
            return None

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("idempotency_key") == idempotency_key:
                        return StoredCitizenSignal(**data)
                except Exception as e:
                    logger.warning("Malformed JSONL line skipped", extra={"safe_context": {"repository": self.__class__.__name__, "line_number": line_number}})
                    continue
        return None

    def store_signals(self, signals: List[StoredCitizenSignal]) -> List[StoredCitizenSignal]:
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                for signal in signals:
                    f.write(signal.model_dump_json() + "\n")
        except Exception as e:
            logger.error("Repository persistence failure", extra={"safe_context": {"repository": self.__class__.__name__, "error_type": type(e).__name__}})
            raise
        return signals

    def load_all(self) -> List[StoredCitizenSignal]:
        if not os.path.exists(self.file_path):
            return []
        signals = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip(): continue
                try:
                    signals.append(StoredCitizenSignal(**json.loads(line)))
                except Exception as e:
                    logger.warning("Malformed JSONL line skipped", extra={"safe_context": {"repository": self.__class__.__name__, "line_number": line_number}})
                    continue
        return signals

synthetic_signal_repository = SyntheticSignalRepository()
