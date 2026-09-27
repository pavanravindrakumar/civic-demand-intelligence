from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime
from backend.app.models.civic_need import NeedType, SectorType

class CitizenDemandEvidence(BaseModel):
    """
    Aggregated and deduplicated evidence of citizen demand.
    Deterministic output grouping validated CivicNeeds.
    """
    demand_id: str

    # Grouping Keys
    canonical_need_type: NeedType
    sector: SectorType
    lgd_village_code: Optional[str] = Field(None, pattern=r"^\d{6}$")

    # Aggregation Window
    aggregation_window_start: datetime
    aggregation_window_end: datetime

    # Aggregation Values
    signal_count: int = Field(ge=0, description="Unique source signal count")
    distinct_submitter_count: int = Field(ge=0, description="Distinct pseudonymous submitters (if available)")
    source_channels: List[str] = Field(description="List of channel diversities")

    # Provenance
    latest_signal_at: datetime
    contributing_signal_ids: List[str]
    aggregation_version: str = "v1"
