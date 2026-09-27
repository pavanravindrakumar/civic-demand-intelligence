from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import hashlib
import uuid

from backend.app.models.signal import CitizenSignalRequest, CitizenSignalResponse, StoredCitizenSignal
from backend.app.data.signal_repository import signal_repository

router = APIRouter(prefix="/api/citizen-signals", tags=["citizen-signals"])

def generate_idempotency_key(source: str, content: str) -> str:
    """Fallback generator for idempotency key if client doesn't provide one."""
    current_time = datetime.now(timezone.utc).isoformat()[:16] # Minute-level precision
    raw = f"{source}-{current_time}-{content[:20]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

@router.post("", response_model=CitizenSignalResponse, status_code=201)
def submit_citizen_signal(request: CitizenSignalRequest):
    """
    Submit a raw citizen signal for processing.
    """
    idempotency_key = request.idempotency_key
    if not idempotency_key:
        idempotency_key = generate_idempotency_key(request.source, request.raw_content)

    # 1. Idempotency Check
    existing_signal = signal_repository.check_idempotency(idempotency_key)
    if existing_signal:
        return CitizenSignalResponse(
            signal_id=existing_signal.signal_id,
            status=existing_signal.extraction_status,
            is_synthetic=existing_signal.is_synthetic,
            submitted_at=existing_signal.submitted_at,
            estimated_processing_time="0 seconds",
            reference_message=f"Duplicate submission detected. Reference ID is: {existing_signal.signal_id}"
        )

    # 2. Validation / Normalization
    if request.lgd_village_code and len(request.lgd_village_code) != 6:
        raise HTTPException(status_code=400, detail="INVALID_INPUT: LGD code must be exactly 6 digits.")

    # 3. Create Stored Signal (Interpretation Pending)
    signal_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    stored = StoredCitizenSignal(
        signal_id=signal_id,
        idempotency_key=idempotency_key,
        source=request.source,
        is_synthetic=request.is_synthetic,
        raw_text=request.raw_content,
        detected_language=request.language_hint,
        extraction_status="RECEIVED",
        submitted_at=now,
        ingested_at=now,
        processing_version="intake.v1.0",
        submitter_pseudonym=str(uuid.uuid4()), # Decoupled identity
        lgd_village_code=request.lgd_village_code
    )

    # 4. Persist (Local JSONL for now)
    try:
        signal_repository.store_signal(stored)
    except Exception as e:
        raise HTTPException(status_code=500, detail="INTERNAL_ERROR: Failed to store signal.")

    # 5. Acknowledge
    return CitizenSignalResponse(
        signal_id=signal_id,
        status="RECEIVED",
        is_synthetic=request.is_synthetic,
        submitted_at=now,
        estimated_processing_time="5-30 seconds",
        reference_message=f"Signal received; interpretation pending. Reference ID is: {signal_id}"
    )
