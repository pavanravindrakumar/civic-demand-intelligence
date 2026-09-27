from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from backend.app.models.civic_need import NeedType, SectorType

ConvergenceState = Literal[
    "CONVERGENCE_IDENTIFIED",
    "PUBLIC_EVIDENCE_ONLY",
    "DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE",
    "INCOMPLETE_CONVERGENCE"
]

SchemeStatus = Literal[
    "NOT_AVAILABLE",
    "FUNDED",
    "PLANNED",
    "IN_PROGRESS",
    "COMPLETED"
]

class ConvergenceOpportunity(BaseModel):
    """
    Evidence-backed Convergence Opportunity representing the intersection of
    unmet demand and potential public infrastructure schemes.
    Does NOT calculate final priority score.
    """
    opportunity_id: str
    assessment_id: str
    lgd_village_code: str

    # Semantic mapping
    canonical_need_type: NeedType
    sector: SectorType

    # States
    convergence_state: ConvergenceState
    scheme_status: SchemeStatus = "NOT_AVAILABLE"

    # Evidence Measurements (Preserved verbatim from upstream)
    reported_household_gap: Optional[int] = Field(None, ge=0)
    household_exposure: Optional[int] = Field(None, ge=0)
    signal_count: Optional[int] = Field(None, ge=0)
    distinct_submitter_count: Optional[int] = Field(None, ge=0)

    # Temporal Alignment
    public_evidence_vintage: Optional[datetime] = None
    demand_aggregation_window_start: Optional[datetime] = None
    demand_aggregation_window_end: Optional[datetime] = None
    evaluated_at: datetime

    # Metadata
    calculation_version: str
