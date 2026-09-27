import uuid
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.models.convergence_opportunity import ConvergenceOpportunity
from backend.app.models.priority_assessment import PriorityAssessment
from backend.app.models.simulator import DemoExecutionScope
from backend.app.analytics.engine import PriorityWeights
from backend.app.data.convergence_repository import ConvergenceOpportunityRepository
from backend.app.data.priority_assessment_repository import PriorityAssessmentRepository

class ConvergencePriorityEngine:
    """
    Deterministic Priority Engine evaluating Convergence Opportunities.
    Uses versioned configuration for weighting. No GenAI logic.
    """

    def __init__(
        self,
        weights: PriorityWeights,
        convergence_repo: ConvergenceOpportunityRepository,
        priority_repo: PriorityAssessmentRepository
    ):
        self.weights = weights
        self.convergence_repo = convergence_repo
        self.priority_repo = priority_repo

        # We reuse configuration structures from existing engine design
        self.MAX_HOUSEHOLDS_CAP = 1000.0
        self.MAX_DEMAND_CAP = 50.0

    def calculate_priorities(self, scope: Optional[DemoExecutionScope] = None) -> List[PriorityAssessment]:
        now = datetime.now(timezone.utc)
        opportunities = self.convergence_repo.load_all()
        assessments: List[PriorityAssessment] = []

        for opp in opportunities:
            if scope and (opp.lgd_village_code != scope.lgd_village_code or opp.canonical_need_type != scope.canonical_need_type):
                continue

            if opp.convergence_state != "CONVERGENCE_IDENTIFIED":
                assessments.append(PriorityAssessment(
                    assessment_id=str(uuid.uuid4()),
                    opportunity_id=opp.opportunity_id,
                    lgd_village_code=opp.lgd_village_code,
                    canonical_need_type=opp.canonical_need_type,
                    sector=opp.sector,
                    priority_score=None,
                    eligibility_status=opp.convergence_state,
                    factor_contributions={},
                    factor_inputs_normalized={},
                    priority_version=self.weights.version,
                    evaluated_at=now
                ))
                continue

            # Normalization
            # 1. Gap
            reported_gap = opp.reported_household_gap or 0
            households = opp.household_exposure or 0

            # Prevent division by zero and bounded ratio
            normalized_gap = (reported_gap / households) if households > 0 else 0.0
            normalized_gap = max(0.0, min(1.0, normalized_gap))

            # 2. Exposure Proxy
            normalized_exposure = households / self.MAX_HOUSEHOLDS_CAP
            normalized_exposure = max(0.0, min(1.0, normalized_exposure))

            # 3. Validated Demand
            signals = float(opp.signal_count or 0)
            normalized_demand = signals / self.MAX_DEMAND_CAP
            normalized_demand = max(0.0, min(1.0, normalized_demand))

            # Weighting
            gap_contribution = normalized_gap * self.weights.infrastructure_gap
            exposure_contribution = normalized_exposure * self.weights.household_exposure
            demand_contribution = normalized_demand * self.weights.validated_demand

            total_score = gap_contribution + exposure_contribution + demand_contribution
            total_score = max(0.0, min(1.0, total_score))

            # Result
            assessments.append(PriorityAssessment(
                assessment_id=str(uuid.uuid4()),
                opportunity_id=opp.opportunity_id,
                lgd_village_code=opp.lgd_village_code,
                canonical_need_type=opp.canonical_need_type,
                sector=opp.sector,
                priority_score=total_score,
                factor_contributions={
                    "gap_contribution": gap_contribution,
                    "exposure_contribution": exposure_contribution,
                    "demand_contribution": demand_contribution
                },
                factor_inputs_normalized={
                    "normalized_gap": normalized_gap,
                    "normalized_exposure": normalized_exposure,
                    "normalized_demand": normalized_demand
                },
                priority_version=self.weights.version,
                evaluated_at=now
            ))

        if scope:
            self.priority_repo.upsert_assessments(assessments)
        else:
            self.priority_repo.overwrite_assessments(assessments)

        return assessments
