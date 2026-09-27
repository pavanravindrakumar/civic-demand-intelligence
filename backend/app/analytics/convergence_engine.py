from typing import List, Optional
import uuid
from datetime import datetime, timezone

from backend.app.models.convergence_opportunity import ConvergenceOpportunity, ConvergenceState, SchemeStatus
from backend.app.models.unmet_demand import UnmetDemandAssessment
from backend.app.models.simulator import DemoExecutionScope
from backend.app.data.unmet_demand_repository import UnmetDemandRepository
from backend.app.data.convergence_repository import ConvergenceOpportunityRepository

class ConvergenceOpportunityEngine:
    CALCULATION_VERSION = "convergence-v1"

    def __init__(
        self,
        unmet_repo: UnmetDemandRepository,
        convergence_repo: ConvergenceOpportunityRepository
    ):
        self.unmet_repo = unmet_repo
        self.convergence_repo = convergence_repo

    def evaluate_opportunities(self, scope: Optional[DemoExecutionScope] = None) -> List[ConvergenceOpportunity]:
        """
        Deterministically evaluates unmet demand assessments into Convergence Opportunities.
        """
        now = datetime.now(timezone.utc)
        assessments = self.unmet_repo.load_all()
        opportunities: List[ConvergenceOpportunity] = []

        for assessment in assessments:
            if scope and (assessment.lgd_village_code != scope.lgd_village_code or assessment.canonical_need_type != scope.canonical_need_type):
                continue

            convergence_state = self._determine_convergence_state(assessment)

            # Since no scheme deterministic status API exists in this MVP for JJM, we explicitly state NOT_AVAILABLE
            scheme_status: SchemeStatus = "NOT_AVAILABLE"

            opp = ConvergenceOpportunity(
                opportunity_id=str(uuid.uuid4()),
                assessment_id=assessment.assessment_id,
                lgd_village_code=assessment.lgd_village_code,
                canonical_need_type=assessment.canonical_need_type,
                sector=assessment.sector,
                convergence_state=convergence_state,
                scheme_status=scheme_status,
                reported_household_gap=assessment.reported_household_gap,
                household_exposure=assessment.household_exposure,
                signal_count=assessment.signal_count,
                distinct_submitter_count=assessment.distinct_submitter_count,
                public_evidence_vintage=assessment.public_evidence_vintage,
                demand_aggregation_window_start=assessment.demand_aggregation_window_start,
                demand_aggregation_window_end=assessment.demand_aggregation_window_end,
                evaluated_at=now,
                calculation_version=self.CALCULATION_VERSION
            )
            opportunities.append(opp)

        if scope:
            self.convergence_repo.upsert_opportunities(opportunities)
        else:
            self.convergence_repo.overwrite_opportunities(opportunities)
        return opportunities

    def _determine_convergence_state(self, assessment: UnmetDemandAssessment) -> ConvergenceState:
        # Check mapping logic from Evidence State
        if assessment.evidence_state == "DEMAND_SUPPORTED":
            # For WATER_SUPPLY_DEFICIT, if there's a household gap reported > 0, it's identified.
            # If household gap == 0, it is INCOMPLETE_CONVERGENCE because public says no gap, but demand says yes.
            # (or it could be DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE if no public record at all, but DEMAND_SUPPORTED implies public record exists)
            if assessment.canonical_need_type == "WATER_SUPPLY_DEFICIT":
                if assessment.reported_household_gap is not None and assessment.reported_household_gap > 0:
                    return "CONVERGENCE_IDENTIFIED"
                else:
                    return "INCOMPLETE_CONVERGENCE"
            return "CONVERGENCE_IDENTIFIED"

        elif assessment.evidence_state == "PUBLIC_EVIDENCE_ONLY":
            return "PUBLIC_EVIDENCE_ONLY"

        elif assessment.evidence_state == "DEMAND_WITHOUT_MATCHING_PUBLIC_EVIDENCE":
            return "DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE"

        elif assessment.evidence_state == "NO_RELEVANT_PUBLIC_EVIDENCE":
            return "DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE"

        return "INCOMPLETE_CONVERGENCE"
