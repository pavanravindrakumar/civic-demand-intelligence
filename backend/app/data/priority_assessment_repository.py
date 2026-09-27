import os
import json
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
from typing import List
from backend.app.models.priority_assessment import PriorityAssessment

class PriorityAssessmentRepository:
    """
    Local development persistence for Priority Assessments.
    Derived artifact, replace rather than append.
    """
    def __init__(self, storage_dir: str = "data/local_development"):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "priority_assessments.jsonl")
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def overwrite_assessments(self, assessments: List[PriorityAssessment]):
        temp_path = self.file_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                for item in assessments:
                    f.write(item.model_dump_json() + "\n")
            os.replace(temp_path, self.file_path)
        except Exception as e:
            logger.error("Repository persistence failure", extra={"safe_context": {"repository": self.__class__.__name__, "error_type": type(e).__name__}})
            raise

    def upsert_assessments(self, assessments: List[PriorityAssessment]):
        existing = self.load_all()
        new_map = {(a.lgd_village_code, a.canonical_need_type): a for a in assessments}
        filtered = [e for e in existing if (e.lgd_village_code, e.canonical_need_type) not in new_map]
        filtered.extend(assessments)
        self.overwrite_assessments(filtered)

    def load_all(self) -> List[PriorityAssessment]:
        if not os.path.exists(self.file_path):
            return []

        results = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    results.append(PriorityAssessment(**data))
                except Exception as e:
                    logger.warning("Malformed JSONL line skipped", extra={"safe_context": {"repository": self.__class__.__name__, "line_number": line_number}})
                    continue
        return results

priority_assessment_repository = PriorityAssessmentRepository()
