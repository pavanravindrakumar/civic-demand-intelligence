# Citizen Signal Contract

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Overview

The Citizen Signal contract defines the interface between:
- **Consumer:** Frontend citizen portal (submits signals)
- **Provider:** Backend FastAPI (`POST /api/signals`)
- **Consumer:** Gemini extraction pipeline (receives sanitized signal)

---

## 2. Signal Submission Request

### Endpoint
```
POST /api/signals
Content-Type: multipart/form-data  (for voice)
Content-Type: application/json     (for text)
Authorization: None (public endpoint)
```

### Text Signal Request

```python
class CitizenSignalTextRequest(BaseModel):
    raw_text:       str = Field(min_length=5, max_length=2000)
    language_hint:  Optional[str] = None    # BCP-47 code, e.g. "hi", "te"
    is_synthetic:   bool = False

    # Idempotency -- client generates this key
    # Format: hash(source + timestamp + first_20_chars_of_text)
    idempotency_key: Optional[str] = None
```

### Voice Signal Request (multipart/form-data)
```
audio_file:      <binary>  (WAV, MP3, OGG, max 5MB)
language_hint:   string    (optional BCP-47)
is_synthetic:    boolean
idempotency_key: string    (optional)
```

---

## 3. Signal Submission Response

### 201 Created (success)
```python
class CitizenSignalResponse(BaseModel):
    signal_id:          str             # UUID for reference
    status:             Literal[
        "RECEIVED",             # stored; extraction queued
        "PROCESSING",           # Gemini extraction in progress
        "COMPLETED",            # extraction done; need identified
        "FAILED",               # extraction failed; signal stored
    ]
    is_synthetic:       bool
    submitted_at:       datetime
    estimated_processing_time: str      # e.g. "5-30 seconds"
    reference_message:  str             # "Your reference ID is: {signal_id}"
```

### Error Responses
```python
class SignalSubmissionError(BaseModel):
    error_code:         str
    message:            str
    field:              Optional[str] = None

# 400 Bad Request
# error_code: "INVALID_INPUT" | "TEXT_TOO_SHORT" | "TEXT_TOO_LONG" | "UNSUPPORTED_FORMAT"
# error_code: "AUDIO_TOO_LARGE" | "INVALID_AUDIO_FORMAT" | "INJECTION_DETECTED"

# 429 Too Many Requests
# error_code: "RATE_LIMIT_EXCEEDED"
# Headers: Retry-After: <seconds>

# 503 Service Unavailable
# error_code: "AI_UNAVAILABLE"
# message: "AI processing temporarily unavailable. Your signal has been saved."
```

---

## 4. Gemini Civic Need Extraction Contract

This is the output contract that Gemini MUST produce. Validated by Pydantic before any further processing.

```python
class CivicNeedExtraction(BaseModel):
    """
    The structured civic need extracted by Gemini from a citizen signal.
    This is the ONLY output Gemini produces for the extraction task.
    Gemini MUST NOT produce any numerical infrastructure statistics.
    """

    # Primary need classification
    need_type: Literal[
        "WATER_SUPPLY_DEFICIT",
        "WATER_QUALITY_ISSUE",
        "ROAD_CONNECTIVITY_DEFICIT",
        "SANITATION_DEFICIT",
        "ELECTRICITY_ACCESS_DEFICIT",
        "HEALTH_FACILITY_DEFICIT",
        "EDUCATION_FACILITY_DEFICIT",
        "OTHER_DEVELOPMENT_NEED",
    ]

    # Human-readable description extracted from the signal
    need_description: str = Field(
        min_length=10,
        max_length=500,
        description="Brief description of the civic need in English. "
                    "Do not fabricate infrastructure statistics."
    )

    # Location as expressed by the citizen (NOT resolved to LGD code by Gemini)
    location_expression: str = Field(
        min_length=2,
        max_length=200,
        description="The location as the citizen expressed it. "
                    "Do not resolve to official codes."
    )
    location_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence that a specific location was identified"
    )

    # Urgency based on tone and content
    urgency: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]

    # Language detection
    detected_language: str = Field(
        description="BCP-47 language code of the input, e.g. 'hi', 'te', 'en'"
    )

    # Multi-need handling
    is_multi_need: bool = Field(
        description="True if the signal expresses multiple distinct civic needs"
    )
    secondary_need_types: Optional[list[str]] = None

    # Extraction notes (for edge cases and reasoning)
    extraction_notes: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Optional notes about ambiguous extraction decisions"
    )
```

**Validation rules enforced after Gemini response:**

| Rule | Code |
|------|------|
| `need_type` must be in the allowlist | Enum validation |
| `location_expression` must not be empty | min_length=2 |
| `location_confidence` must be 0.0-1.0 | Field constraint |
| No URL patterns in description | Regex check |
| No numeric infrastructure values in description | Pattern check |
| `detected_language` must be a valid BCP-47 code | Format check |

---

## 5. Signal Storage Contract (BigQuery)

After validation, the signal is stored with these fields:

```python
class StoredCitizenSignal(BaseModel):
    signal_id:              str             # UUID (system-generated)
    idempotency_key:        str             # hash for dedup
    source:                 Literal["WEB_FORM", "VOICE", "API", "SYNTHETIC"]
    is_synthetic:           bool
    source_signal_id:       Optional[str]

    # Input content
    raw_text:               Optional[str]   # sanitized input text
    audio_gcs_ref:          Optional[str]   # GCS URI (audio only; deleted after 24h)
    detected_language:      Optional[str]   # from Gemini extraction

    # Extraction output
    extraction_status:      Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
    extracted_need_type:    Optional[str]   # from CivicNeedExtraction
    extracted_location:     Optional[str]   # from CivicNeedExtraction
    extraction_notes:       Optional[str]

    # Provenance
    submitted_at:           datetime
    ingested_at:            datetime
    processing_version:     str             # e.g. "extraction.v1.0"
    submitter_pseudonym:    Optional[str]   # random session UUID; not linked to identity
```

---

## 6. Idempotency

The system uses `idempotency_key` to prevent duplicate signal processing.

**Key generation (client-side):**
```javascript
idempotencyKey = hash(
    source +
    submittedAt.toISOString().slice(0, 16) +  // minute-level precision
    rawText.slice(0, 20)
)
```

**Server-side check:**
```python
# Before storing, check for existing signal with same idempotency_key
existing = bq_client.query(
    "SELECT signal_id FROM citizen_signals WHERE idempotency_key = @key",
    {"key": idempotency_key}
)
if existing:
    return SignalSubmissionResponse(signal_id=existing.signal_id, status="RECEIVED")
```

---

## 7. Rate Limiting

```
Citizen signal submission:
  5 requests per IP per hour
  Implementation: Redis or in-memory counter (FastAPI middleware)

Response on limit exceeded:
  HTTP 429
  Retry-After: <seconds until reset>
  Body: {"error_code": "RATE_LIMIT_EXCEEDED", "message": "..."}
```

---

## 8. Error States

| Error Code | HTTP | Meaning |
|-----------|------|---------|
| `INVALID_INPUT` | 400 | Input fails schema validation |
| `TEXT_TOO_SHORT` | 400 | Less than 5 characters |
| `TEXT_TOO_LONG` | 400 | More than 2000 characters |
| `UNSUPPORTED_FORMAT` | 400 | Audio format not WAV/MP3/OGG |
| `AUDIO_TOO_LARGE` | 400 | Audio exceeds 5MB |
| `INJECTION_DETECTED` | 400 | Disallowed content pattern detected |
| `RATE_LIMIT_EXCEEDED` | 429 | IP rate limit hit |
| `AI_UNAVAILABLE` | 503 | Gemini API unavailable (signal still saved) |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

*Architecture V1 -- 2026-09-24*
