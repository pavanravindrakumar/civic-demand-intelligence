# Security Architecture

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Threat Model Summary

| Threat | Actor | Risk | Mitigation |
|--------|-------|------|-----------|
| Prompt injection | Malicious citizen | HIGH | Input sanitization + schema enforcement |
| LLM hallucination | System | HIGH | Strict schema + backend validation + data separation |
| Synthetic data contamination | Careless tester | HIGH | Mandatory `is_synthetic` flag; UI labeling |
| PII exposure | Data breach | HIGH | No PII collected; pseudonymous IDs only |
| Unauthorized dashboard access | External attacker | HIGH | Firebase Auth + role-based access |
| Copilot tool abuse | Authenticated user | MEDIUM | Allowlist + typed schemas + rate limiting |
| Audio data retention | Regulatory / privacy | MEDIUM | Short retention policy + no personal linkage |
| Government data manipulation | Insider | MEDIUM | Immutable evidence ledger + audit trail |
| SQL injection via Copilot | Malicious policymaker | LOW | No freeform SQL; all queries parameterized |
| Source data spoofing | Compromised pipeline | LOW | Snapshot provenance + ingested_at tracking |

---

## 2. Authentication and Authorization

### 2.1 Authentication Strategy

**Firebase Authentication** with Google provider (mandatory for policymaker dashboard).

| User Role | Auth Method | Access |
|-----------|------------|--------|
| Citizen | None (anonymous) | Signal submission only |
| Policymaker | Google OAuth via Firebase | Full dashboard access |
| Admin | Google OAuth + custom claim | Admin panel + weight configuration |
| Ingest Service | Service account key | BigQuery write access |

### 2.2 Authorization Rules

```
Citizen routes:  /citizen/**
  - No auth required
  - Rate limited: 5 signals per IP per hour

Policymaker routes: /dashboard/**
  - Firebase ID token required
  - Token validated server-side on every API request
  - Expired tokens rejected (no silent refresh on backend)

Admin routes: /admin/**
  - Firebase ID token + custom claim "role=admin" required
  - Future: separate admin service account

Copilot API: /api/copilot/**
  - Firebase ID token required
  - Rate limit: 20 queries per user per hour
  - All tool executions logged with user ID (pseudonymous)
```

### 2.3 Backend Token Validation

```python
async def verify_firebase_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing auth token")
    token = authorization[7:]
    try:
        decoded = firebase_admin.auth.verify_id_token(token)
        return decoded
    except firebase_admin.auth.ExpiredIdTokenError:
        raise HTTPException(401, "Token expired")
    except Exception:
        raise HTTPException(401, "Invalid token")
```

---

## 3. Input Sanitization and Prompt Injection Defense

### 3.1 Citizen Text Input

All citizen text input is processed before reaching Gemini:

```python
def sanitize_citizen_input(raw_text: str) -> str:
    # 1. Length limit
    if len(raw_text) > 2000:
        raise ValidationError("Input too long")

    # 2. Strip HTML/markdown to prevent injection via formatting
    text = bleach.clean(raw_text, tags=[], strip=True)

    # 3. Detect and reject obvious injection patterns
    INJECTION_PATTERNS = [
        r"ignore previous",
        r"forget instructions",
        r"system prompt",
        r"DROP TABLE",
        r"SELECT \*",
        r"<script",
    ]
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValidationError("Input contains disallowed content")

    return text.strip()
```

### 3.2 Prompt Construction Safety

```python
# CORRECT: Use message roles, never string concatenation
messages = [
    {
        "role": "system",
        "content": EXTRACTION_SYSTEM_PROMPT  # never user-controlled
    },
    {
        "role": "user",
        "content": sanitize_citizen_input(raw_text)  # sanitized user content
    }
]
```

### 3.3 Structured Output Defense

The `response_schema` parameter forces Gemini to output only a valid JSON object matching the Pydantic schema. This eliminates:
- Freeform text injection in response
- Tool call spoofing in extraction mode
- Schema field injection attacks

---

## 4. PII Minimization

| Data Type | Collection | Retention | Notes |
|-----------|-----------|----------|-------|
| Citizen name | NEVER | N/A | Not requested at any step |
| Phone number | NEVER | N/A | Not requested |
| Email | NEVER | N/A | Not requested |
| Address (raw) | NEVER | N/A | Location extracted as village/district only |
| Audio recording | Yes (temporary) | 24 hours max | GCS with TTL; no personal linkage |
| Session pseudonym | Optional | Session only | Random UUID; not linked to identity |
| IP address | Logs only | 7 days max | For rate limiting; not stored in BQ |
| LGD code (geographic) | Yes | Permanent | Administrative geography -- not personal |

**The system is designed so that individual citizen identity cannot be reconstructed from stored data.**

---

## 5. Audio Data Security

1. Audio uploaded to Cloud Storage with a random UUID filename (no original filename preserved)
2. Audio GCS path stored in `citizen_signals.audio_gcs_ref`
3. GCS bucket has a **24-hour object lifecycle policy** -- audio auto-deleted after Gemini extraction
4. GCS object has no public access -- accessible only via signed URL or service account
5. Audio is NEVER stored in BigQuery
6. No voice biometric analysis performed
7. Transcription (if produced) is not stored separately -- only the structured extraction output

---

## 6. Synthetic Data Contamination Prevention

The `is_synthetic` flag is the primary defense. Additional safeguards:

1. `is_synthetic` defaults to `TRUE` in development environment (no accidental real data)
2. Production environment: `is_synthetic` defaults to `FALSE` and cannot be set to `FALSE` via API without admin authorization
3. All analytics queries have a `include_synthetic` parameter that defaults to `FALSE` for policymaker views
4. The evidence ledger records `is_synthetic` at every step
5. Priority scores are calculated separately for `organic_demand_count` and `synthetic_demand_count`
6. UI always shows "[SYNTHETIC: N of M signals are test data]" when synthetic signals are present

---

## 7. Evidence Integrity

The evidence ledger is **append-only** by design:

```sql
-- Evidence ledger table has NO UPDATE or DELETE permissions for any service account
-- All corrections are made by inserting a new superseding entry
INSERT INTO evidence_ledger (
  ledger_id, report_id, step_type, ..., supersedes_ledger_id
) VALUES (...);
```

GAP and priority calculations are **immutable once recorded**:
- A new calculation always creates a new record with a new ID
- The previous record is preserved with its original `calculation_version`
- Reports reference specific ledger entries, not mutable derived values

---

## 8. Copilot Security Controls

All Copilot tool executions:
1. Validated against tool allowlist (hard-coded; not user-configurable)
2. Arguments validated against typed Pydantic schemas
3. No freeform SQL accepted by any tool
4. All arguments are string or integer (no code execution)
5. Results are read-only BigQuery queries using parameterized queries
6. Tool execution logs stored with user pseudonym and timestamp
7. Gemini response is inspected for injected statistics before display

**Rate limits:**
- 20 Copilot queries per user per hour
- 100 Copilot queries per user per day
- 5 tool calls per Copilot conversation turn

---

## 9. Secret Management

All API keys and credentials stored in **Google Secret Manager**:

| Secret | Usage |
|--------|-------|
| `GEMINI_API_KEY` | Gemini API (Google AI Studio) |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase Admin SDK |
| `BIGQUERY_SERVICE_ACCOUNT` | BigQuery read/write |
| `MAPS_API_KEY` | Google Maps Platform |
| `GCS_SERVICE_ACCOUNT` | Cloud Storage audio bucket |

No secrets in environment variables in production. All loaded from Secret Manager at startup via the Cloud Run service account.

**Development:** `.env` file (gitignored) with test/dev keys only.

---

## 10. Security Headers

FastAPI backend configured with:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # strict -- no wildcard
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Next.js frontend headers (next.config.js):
```javascript
Content-Security-Policy: default-src 'self'; script-src 'self'; connect-src 'self' https://api.your-domain.com https://maps.googleapis.com;
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

---

## 11. Audit Trail

Every significant action is logged:

| Event | Log Level | Storage |
|-------|----------|---------|
| Signal submitted | INFO | BigQuery citizen_signals |
| Gemini extraction | INFO | BigQuery citizen_signals (processing_version) |
| Geography resolution | INFO | BigQuery geography_resolution_log |
| Gap calculated | INFO | BigQuery gap_assessments |
| Copilot tool executed | INFO | Cloud Logging (with user pseudonym) |
| Auth failure | WARN | Cloud Logging |
| Validation failure | WARN | Cloud Logging |
| Injection pattern detected | ERROR | Cloud Logging + alert |

---

## 12. Data Residency

All services configured in the `asia-south1` (Mumbai) region:
- BigQuery dataset
- Cloud Storage bucket
- Cloud Run services
- Secret Manager secrets

This keeps data within India for regulatory comfort, though formal government data compliance is out of MVP scope.

---

*Architecture V1 -- 2026-09-24*
