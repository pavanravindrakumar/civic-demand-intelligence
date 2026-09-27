import os
import json
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
import uuid
from typing import Optional
from datetime import datetime, timezone
from backend.app.models.signal import StoredCitizenSignal

class SignalRepository:
    """
    Local development persistence mechanism for Citizen Signals.
    Appends to a JSONL file in the local development directory.
    Designed to be easily replaceable with BigQuery or similar in production.
    """
    def __init__(self, storage_dir: str = "data/local_development"):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "signals.jsonl")
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def check_idempotency(self, idempotency_key: str) -> Optional[StoredCitizenSignal]:
        """
        Checks if a signal with the given idempotency key already exists.
        Returns the existing signal if found, otherwise None.
        """
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

    def store_signal(self, signal: StoredCitizenSignal) -> StoredCitizenSignal:
        """
        Appends the signal to the local JSONL file.
        """
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(signal.model_dump_json() + "\n")
        except Exception as e:
            logger.error("Repository persistence failure", extra={"safe_context": {"repository": self.__class__.__name__, "error_type": type(e).__name__}})
            raise
        return signal

signal_repository = SignalRepository()
