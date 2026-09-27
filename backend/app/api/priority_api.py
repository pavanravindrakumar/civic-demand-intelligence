from fastapi import APIRouter, Query, Path, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

from backend.app.models.civic_need import NeedType, SectorType
from backend.app.models.priority_assessment import PriorityAssessment
from backend.app.data.priority_assessment_repository import priority_assessment_repository
from backend.app.analytics.engine import PriorityWeights

router = APIRouter(prefix="/api/priority/assessments", tags=["Priority Engine"])

class FactorExplanation(BaseModel):
    normalized_input: float
    configured_weight: float
    contribution: float

class PriorityAssessmentResponse(BaseModel):
    priority_assessment_id: str
    opportunity_id: str
    lgd_village_code: str
    canonical_need_type: NeedType
    sector: SectorType
    priority_score: Optional[float]
    priority_version: str
    calculation_version: str = "v1.0"
    eligibility_status: str

    # Explanations for the UI
    factors: Dict[str, FactorExplanation]

    # Evidence references
    citizen_evidence_provenance: str = "SYNTHETIC_DEMO_SIGNAL"  # Could be derived from ledger or upstream in a robust way, here we set default for demo
    public_evidence_provenance: str = "REAL_JJM_LGD"

    evaluated_at: datetime


def _build_response(assessment: PriorityAssessment, weights: PriorityWeights) -> PriorityAssessmentResponse:
    factors = {}
    if assessment.priority_score is not None:
        # We know exactly the 3 active factors
        if "normalized_gap" in assessment.factor_inputs_normalized:
            factors["infrastructure_gap"] = FactorExplanation(
                normalized_input=assessment.factor_inputs_normalized.get("normalized_gap", 0.0),
                configured_weight=weights.infrastructure_gap,
                contribution=assessment.factor_contributions.get("gap_contribution", 0.0)
            )
        if "normalized_exposure" in assessment.factor_inputs_normalized:
            factors["household_exposure"] = FactorExplanation(
                normalized_input=assessment.factor_inputs_normalized.get("normalized_exposure", 0.0),
                configured_weight=weights.household_exposure,
                contribution=assessment.factor_contributions.get("exposure_contribution", 0.0)
            )
        if "normalized_demand" in assessment.factor_inputs_normalized:
            factors["validated_demand"] = FactorExplanation(
                normalized_input=assessment.factor_inputs_normalized.get("normalized_demand", 0.0),
                configured_weight=weights.validated_demand,
                contribution=assessment.factor_contributions.get("demand_contribution", 0.0)
            )

    return PriorityAssessmentResponse(
        priority_assessment_id=assessment.assessment_id,
        opportunity_id=assessment.opportunity_id,
        lgd_village_code=assessment.lgd_village_code,
        canonical_need_type=assessment.canonical_need_type,
        sector=assessment.sector,
        priority_score=assessment.priority_score,
        priority_version=assessment.priority_version,
        eligibility_status=assessment.eligibility_status,
        factors=factors,
        evaluated_at=assessment.evaluated_at
    )


@router.get("", response_model=List[PriorityAssessmentResponse])
def get_priority_assessments(
    lgd_village_code: Optional[str] = Query(None, pattern=r"^\d{6}$"),
    canonical_need_type: Optional[NeedType] = None,
    sector: Optional[SectorType] = None,
    priority_version: Optional[str] = None,
    eligibility_status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """
    Retrieve read-only Priority Assessments.
    Records are deterministically ordered by score (descending) then evaluated_at.
    """
    all_assessments = priority_assessment_repository.load_all()
    weights = PriorityWeights()

    filtered = []
    for a in all_assessments:
        if lgd_village_code and a.lgd_village_code != lgd_village_code:
            continue
        if canonical_need_type and a.canonical_need_type != canonical_need_type:
            continue
        if sector and a.sector != sector:
            continue
        if priority_version and a.priority_version != priority_version:
            continue
        if eligibility_status and a.eligibility_status != eligibility_status:
            continue

        filtered.append(a)

    # Sort: highest score first, then newest
    def sort_key(a: PriorityAssessment):
        score = a.priority_score if a.priority_score is not None else -1.0
        return (-score, -a.evaluated_at.timestamp(), a.assessment_id)

    filtered.sort(key=sort_key)

    return [_build_response(a, weights) for a in filtered[:limit]]


@router.get("/{priority_assessment_id}", response_model=PriorityAssessmentResponse)
def get_priority_assessment_detail(priority_assessment_id: str = Path(...)):
    """
    Retrieve specific priority assessment by ID.
    """
    all_assessments = priority_assessment_repository.load_all()
    weights = PriorityWeights()

    for a in all_assessments:
        if a.assessment_id == priority_assessment_id:
            return _build_response(a, weights)

    raise HTTPException(status_code=404, detail="Priority Assessment not found")
