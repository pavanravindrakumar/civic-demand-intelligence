from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from backend.app.models.civic_need import NeedType, SectorType

class PriorityAssessment(BaseModel):
    """
    Deterministic priority scoring based on Convergence Opportunity.
    Bounded to 0.0-1.0. No probabilistic model reasoning.
    """
    assessment_id: str
    opportunity_id: str
    lgd_village_code: str

    # Semantic mapping
    canonical_need_type: NeedType
    sector: SectorType

    # Scoring
    priority_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    eligibility_status: str = "CONVERGENCE_IDENTIFIED"

    # Factor Contributions (For auditable Evidence Ledger)
    factor_contributions: Dict[str, float]
    factor_inputs_normalized: Dict[str, float]

    # Configuration
    priority_version: str

    # Timestamps
    evaluated_at: datetime
