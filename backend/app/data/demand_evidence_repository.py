import os
import json
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
from typing import List
from backend.app.models.demand_evidence import CitizenDemandEvidence

class CitizenDemandEvidenceRepository:
    """
    Local development persistence for derived Citizen Demand Evidence.
    Since this is a derived artifact (rebuildable), the main operation is replacing
    the artifact rather than appending to it.
    """
    def __init__(self, storage_dir: str = "data/local_development"):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "citizen_demand_evidence.jsonl")
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def overwrite_evidence(self, aggregates: List[CitizenDemandEvidence]):
        """
        Overwrites the entire derived artifact with the newly calculated aggregates.
        """
        temp_path = self.file_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                for agg in aggregates:
                    f.write(agg.model_dump_json() + "\n")
            # Atomic replace
            os.replace(temp_path, self.file_path)
        except Exception as e:
            logger.error("Repository persistence failure", extra={"safe_context": {"repository": self.__class__.__name__, "error_type": type(e).__name__}})
            raise

    def load_all(self) -> List[CitizenDemandEvidence]:
        """
        Reads all existing aggregates.
        """
        if not os.path.exists(self.file_path):
            return []

        aggregates = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    aggregates.append(CitizenDemandEvidence(**data))
                except Exception as e:
                    logger.warning("Malformed JSONL line skipped", extra={"safe_context": {"repository": self.__class__.__name__, "line_number": line_number}})
                    continue
        return aggregates

demand_evidence_repository = CitizenDemandEvidenceRepository()
