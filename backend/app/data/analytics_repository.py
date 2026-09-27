import csv
from backend.app.core.logging import get_logger
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = get_logger(__name__)

# Project root is 4 levels above this file:
# backend/app/data/analytics_repository.py -> backend/app/data -> backend/app -> backend -> project_root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CSV_PATH = _PROJECT_ROOT / "data" / "normalized" / "normalized_villages.csv"

from backend.app.analytics.engine import (
    CivicAnalyticsEngine, PriorityWeights, VillageInput, PriorityResult, ReadinessState
)

class AnalyticsSummary(BaseModel):
    total_villages_analyzed: int
    total_households: int
    total_fhtc: int
    total_reported_household_gap: int
    readiness_state: ReadinessState
    calculation_version: str
    data_source: str = "LOCAL_CSV"

class AnalyticsRepository:
    """
    Data access abstraction for Analytics.
    Currently uses local CSV for MVP development phase to avoid repeated BQ costs.
    Designed so it can be swapped for a BigQuery implementation later without altering the API contract.
    """

    def __init__(self, csv_path: Optional[str] = None):
        # Resolve path: explicit argument overrides the default project-root-relative path.
        # Using __file__-relative resolution means the data file is found regardless of
        # which directory the uvicorn process is started from.
        if csv_path is not None:
            self.csv_path = csv_path
        else:
            self.csv_path = str(_DEFAULT_CSV_PATH)

        if not os.path.exists(self.csv_path):
            logger.warning(
                "Analytics CSV not found at resolved path. "
                "Data-dependent endpoints will return empty results. "
                "Expected location: data/normalized/normalized_villages.csv under project root."
            )
        self._engine = CivicAnalyticsEngine(PriorityWeights())
        self._data: Dict[str, PriorityResult] = {}
        self._summary: Optional[AnalyticsSummary] = None
        self._loaded = False

    def _load_data(self):
        if self._loaded:
            return

        total_villages = 0
        total_hh = 0
        total_fhtc = 0
        total_gap = 0

        # Determine global readiness. Since we have no citizen demand in the MVP dataset,
        # it will be PUBLIC_EVIDENCE_ONLY.
        global_readiness = ReadinessState.PUBLIC_EVIDENCE_ONLY

        if os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row_num, row in enumerate(reader, 2):
                        try:
                            hh = int(row['households'])
                            fhtc = int(row['fhtc_house_connections'])
                            gap = int(row['reported_household_gap'])
                            lgd_code = row['lgd_village_code']

                            inp = VillageInput(
                                lgd_village_code=lgd_code,
                                households=hh,
                                fhtc_house_connections=fhtc,
                                reported_household_gap=gap,
                                validated_citizen_demand_count=None,
                                data_valid=row['data_valid'].lower() == 'true'
                            )

                            res = self._engine.assess_village(inp)
                            if res.readiness != ReadinessState.INVALID_INPUTS:
                                self._data[lgd_code] = res
                                total_villages += 1
                                total_hh += hh
                                total_fhtc += fhtc
                                total_gap += gap

                        except ValueError:
                            logger.warning("Malformed row skipped in analytics data", extra={"safe_context": {"repository": "AnalyticsRepository", "row_number": row_num}})
                            continue
            except Exception as e:
                logger.error("External data failure", extra={"safe_context": {"operation": "load_analytics_data", "error_type": type(e).__name__}})

        self._summary = AnalyticsSummary(
            total_villages_analyzed=total_villages,
            total_households=total_hh,
            total_fhtc=total_fhtc,
            total_reported_household_gap=total_gap,
            readiness_state=global_readiness,
            calculation_version=self._engine.CALCULATION_VERSION
        )
        self._loaded = True

    def get_summary(self) -> AnalyticsSummary:
        self._load_data()
        return self._summary

    def get_village_analytics(self, lgd_village_code: str) -> Optional[PriorityResult]:
        self._load_data()
        return self._data.get(lgd_village_code)
