from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

from backend.app.models.civic_need import NeedType, SectorType

EvidenceState = Literal[
    "PUBLIC_EVIDENCE_ONLY",
    "DEMAND_SUPPORTED",
    "DEMAND_WITHOUT_MATCHING_PUBLIC_EVIDENCE",
    "NO_RELEVANT_PUBLIC_EVIDENCE"
]

class UnmetDemandAssessment(BaseModel):
    """
    Deterministic synthesis of public infrastructure evidence and citizen demand evidence.
    Does NOT calculate final priority, Unmet Demand is an evidence convergence state.
    """
    assessment_id: str
    lgd_village_code: str

    # Semantic Alignment
    canonical_need_type: NeedType
    sector: SectorType

    # Evidence State
    evidence_state: EvidenceState

    # Public Evidence Measurements
    public_evidence_vintage: Optional[datetime] = None
    reported_household_gap: Optional[int] = Field(
        None, ge=0,
        description="Publicly reported gap (e.g. households without water taps). Do not mix with signal count."
    )
    household_exposure: Optional[int] = Field(
        None, ge=0,
        description="Total households in the village from public data."
    )

    # Citizen Demand Evidence Measurements
    demand_aggregation_window_start: Optional[datetime] = None
    demand_aggregation_window_end: Optional[datetime] = None
    signal_count: Optional[int] = Field(
        None, ge=0,
        description="Number of interpreted citizen signals. Do not subtract from household gap."
    )
    distinct_submitter_count: Optional[int] = Field(
        None, ge=0,
        description="Distinct pseudonyms submitting signals."
    )

    # Assessment Metadata
    assessment_date: datetime
    assessment_version: str
