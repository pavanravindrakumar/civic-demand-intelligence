import os
import json
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
from typing import List
from backend.app.models.convergence_opportunity import ConvergenceOpportunity

class ConvergenceOpportunityRepository:
    """
    Local development persistence for derived Convergence Opportunities.
    Derived artifact, replace rather than append.
    """
    def __init__(self, storage_dir: str = "data/local_development"):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "convergence_opportunities.jsonl")
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def overwrite_opportunities(self, opportunities: List[ConvergenceOpportunity]):
        """
        Overwrites the entire derived artifact.
        """
        temp_path = self.file_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                for item in opportunities:
                    f.write(item.model_dump_json() + "\n")
            os.replace(temp_path, self.file_path)
        except Exception as e:
            logger.error("Repository persistence failure", extra={"safe_context": {"repository": self.__class__.__name__, "error_type": type(e).__name__}})
            raise

    def upsert_opportunities(self, opportunities: List[ConvergenceOpportunity]):
        existing = self.load_all()
        new_map = {(a.lgd_village_code, a.canonical_need_type): a for a in opportunities}
        filtered = [e for e in existing if (e.lgd_village_code, e.canonical_need_type) not in new_map]
        filtered.extend(opportunities)
        self.overwrite_opportunities(filtered)

    def load_all(self) -> List[ConvergenceOpportunity]:
        if not os.path.exists(self.file_path):
            return []

        results = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    results.append(ConvergenceOpportunity(**data))
                except Exception as e:
                    logger.warning("Malformed JSONL line skipped", extra={"safe_context": {"repository": self.__class__.__name__, "line_number": line_number}})
                    continue
        return results

convergence_repository = ConvergenceOpportunityRepository()
