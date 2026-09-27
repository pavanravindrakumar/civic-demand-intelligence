from typing import List, Dict, Tuple, Optional
import uuid
from datetime import datetime, timezone

from backend.app.models.civic_need import NeedType, SectorType, get_sector_for_need
from backend.app.models.simulator import DemoExecutionScope
from backend.app.models.demand_evidence import CitizenDemandEvidence
from backend.app.models.unmet_demand import UnmetDemandAssessment, EvidenceState
from backend.app.data.analytics_repository import AnalyticsRepository
from backend.app.data.demand_evidence_repository import CitizenDemandEvidenceRepository
from backend.app.data.unmet_demand_repository import UnmetDemandRepository

class UnmetDemandAssessmentEngine:
    CALCULATION_VERSION = "unmet-v1"

    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        demand_repo: CitizenDemandEvidenceRepository,
        unmet_repo: UnmetDemandRepository
    ):
        self.analytics_repo = analytics_repo
        self.demand_repo = demand_repo
        self.unmet_repo = unmet_repo

    def run_assessment(self, scope: Optional[DemoExecutionScope] = None) -> List[UnmetDemandAssessment]:
        """
        Deterministically assesses unmet demand by joining public evidence and citizen demand.
        Returns the rebuilt list of assessments and persists them locally.
        """
        now = datetime.now(timezone.utc)
        assessments: List[UnmetDemandAssessment] = []

        # 1. Load data
        # We access the internal _data dictionary for performance, or we can iterate if a method exists.
        # Since analytics_repo._data is populated after load_data, we'll force load and use it.
        self.analytics_repo._load_data()
        public_data = self.analytics_repo._data

        demand_data = self.demand_repo.load_all()

        # Map demand by (lgd_village_code, canonical_need_type)
        # Note: we ignore UNRESOLVED geography since we cannot attach it to a village.
        demand_map: Dict[Tuple[str, NeedType], CitizenDemandEvidence] = {}
        for d in demand_data:
            if d.lgd_village_code:
                demand_map[(d.lgd_village_code, d.canonical_need_type)] = d

        # 2. Process Public Evidence Base (Water)
        # Currently, public evidence is solely JJM water data.
        # So it applies strictly to WATER_SUPPLY_DEFICIT.
        WATER_NEED: NeedType = "WATER_SUPPLY_DEFICIT"

        for lgd_code, pub_ev in public_data.items():
            if scope and (lgd_code != scope.lgd_village_code or WATER_NEED != scope.canonical_need_type):
                continue

            key = (lgd_code, WATER_NEED)
            dem_ev = demand_map.get(key)

            state: EvidenceState = "DEMAND_SUPPORTED" if dem_ev else "PUBLIC_EVIDENCE_ONLY"

            assessment = UnmetDemandAssessment(
                assessment_id=str(uuid.uuid4()),
                lgd_village_code=lgd_code,
                canonical_need_type=WATER_NEED,
                sector="WATER",
                evidence_state=state,
                public_evidence_vintage=now, # In a real system, track source dataset vintage
                reported_household_gap=pub_ev.reported_household_gap,
                household_exposure=pub_ev.household_exposure,
                demand_aggregation_window_start=dem_ev.aggregation_window_start if dem_ev else None,
                demand_aggregation_window_end=dem_ev.aggregation_window_end if dem_ev else None,
                signal_count=dem_ev.signal_count if dem_ev else None,
                distinct_submitter_count=dem_ev.distinct_submitter_count if dem_ev else None,
                assessment_date=now,
                assessment_version=self.CALCULATION_VERSION
            )
            assessments.append(assessment)

            # Remove from demand map so we don't process it again
            if dem_ev:
                del demand_map[key]

        # 3. Process Remaining Citizen Demand (No matching public evidence or different need type)
        for (lgd_code, need_type), dem_ev in demand_map.items():
            if scope and (lgd_code != scope.lgd_village_code or need_type != scope.canonical_need_type):
                continue

            if need_type == WATER_NEED:
                # Water need but no public evidence for this village
                state = "DEMAND_WITHOUT_MATCHING_PUBLIC_EVIDENCE"
            else:
                # Other need types have no relevant public evidence in the system currently
                state = "NO_RELEVANT_PUBLIC_EVIDENCE"

            assessment = UnmetDemandAssessment(
                assessment_id=str(uuid.uuid4()),
                lgd_village_code=lgd_code,
                canonical_need_type=need_type,
                sector=dem_ev.sector,
                evidence_state=state,
                public_evidence_vintage=None,
                reported_household_gap=None,
                household_exposure=None,
                demand_aggregation_window_start=dem_ev.aggregation_window_start,
                demand_aggregation_window_end=dem_ev.aggregation_window_end,
                signal_count=dem_ev.signal_count,
                distinct_submitter_count=dem_ev.distinct_submitter_count,
                assessment_date=now,
                assessment_version=self.CALCULATION_VERSION
            )
            assessments.append(assessment)

        # 4. Upsert/Overwrite derived artifact
        if scope:
            self.unmet_repo.upsert_assessments(assessments)
        else:
            self.unmet_repo.overwrite_assessments(assessments)

        return assessments
