from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class CitizenSignalRequest(BaseModel):
    source: Literal["TEXT", "VOICE", "MESSAGING", "SIMULATOR", "WEB_FORM", "API"]
    raw_content: str = Field(min_length=5, max_length=2000)
    language_hint: Optional[str] = None
    is_synthetic: bool = False
    idempotency_key: Optional[str] = None

    # Geography hint if the citizen provided LGD directly
    lgd_village_code: Optional[str] = Field(None, pattern=r"^\d{6}$")

class CitizenSignalResponse(BaseModel):
    signal_id: str
    status: Literal["RECEIVED", "PROCESSING", "COMPLETED", "FAILED"]
    is_synthetic: bool
    submitted_at: datetime
    estimated_processing_time: str
    reference_message: str

class StoredCitizenSignal(BaseModel):
    signal_id: str
    idempotency_key: str
    source: str
    is_synthetic: bool
    provenance: str = "OFFICIAL"
    synthetic_scenario_id: Optional[str] = None

    raw_text: Optional[str] = None
    detected_language: Optional[str] = None

    extraction_status: str
    extracted_need_type: Optional[str] = None
    extracted_location: Optional[str] = None
    extraction_notes: Optional[str] = None

    submitted_at: datetime
    ingested_at: datetime
    processing_version: str
    submitter_pseudonym: Optional[str] = None

    # Optional explicitly provided geography
    lgd_village_code: Optional[str] = None
