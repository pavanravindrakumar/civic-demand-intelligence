from pydantic import BaseModel, Field, constr, ConfigDict
from typing import Literal, Optional, List
from datetime import datetime

NeedType = Literal[
    "WATER_SUPPLY_DEFICIT",
    "WATER_QUALITY_ISSUE",
    "ROAD_CONNECTIVITY_DEFICIT",
    "SANITATION_DEFICIT",
    "ELECTRICITY_ACCESS_DEFICIT",
    "HEALTH_FACILITY_DEFICIT",
    "EDUCATION_FACILITY_DEFICIT",
    "OTHER_DEVELOPMENT_NEED",
]

SectorType = Literal["WATER", "ROADS", "SANITATION", "ELECTRICITY", "HEALTH", "EDUCATION", "OTHER"]

class CivicNeedExtraction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """
    The structured civic need extracted by Gemini from a citizen signal.
    """
    need_type: NeedType
    need_description: str = Field(
        min_length=10,
        max_length=500,
        description="Brief description of the civic need in English. Do not fabricate infrastructure statistics."
    )
    location_expression: str = Field(
        min_length=2,
        max_length=200,
        description="The location as the citizen expressed it. Do not resolve to official codes."
    )
    location_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence that a specific location was identified"
    )
    urgency: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    detected_language: str = Field(
        description="BCP-47 language code of the input, e.g. 'hi', 'te', 'en'"
    )
    is_multi_need: bool = Field(
        description="True if the signal expresses multiple distinct civic needs"
    )
    secondary_need_types: Optional[List[NeedType]] = None
    extraction_notes: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Optional notes about ambiguous extraction decisions"
    )

class CivicNeed(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """
    The normalized, canonical representation of a civic development need.
    """
    need_id: str
    source_signal_id: str
    source_channel: str = "UNKNOWN"
    submitter_pseudonym: Optional[str] = None

    canonical_need_type: NeedType
    sector: SectorType

    need_label_en: str
    need_description: Optional[str] = None

    is_composite: bool = False
    related_need_ids: List[str] = []

    # Location
    location_expression: str
    location_confidence: float
    lgd_village_code: Optional[str] = Field(None, pattern=r"^\d{6}$")

    # Status/Provenance
    detected_language: str
    urgency: str

    first_seen_at: datetime
    last_updated_at: datetime
    processing_version: str

def get_sector_for_need(need_type: NeedType) -> SectorType:
    mapping = {
        "WATER_SUPPLY_DEFICIT": "WATER",
        "WATER_QUALITY_ISSUE": "WATER",
        "ROAD_CONNECTIVITY_DEFICIT": "ROADS",
        "SANITATION_DEFICIT": "SANITATION",
        "ELECTRICITY_ACCESS_DEFICIT": "ELECTRICITY",
        "HEALTH_FACILITY_DEFICIT": "HEALTH",
        "EDUCATION_FACILITY_DEFICIT": "EDUCATION",
        "OTHER_DEVELOPMENT_NEED": "OTHER",
    }
    return mapping.get(need_type, "OTHER")
