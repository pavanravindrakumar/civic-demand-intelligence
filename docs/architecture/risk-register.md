# Risk Register

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## Failure / Fallback Matrix

### Critical External Dependencies

| Dependency | Primary Path | Failure Mode | Fallback | Remaining Functional |
|-----------|-------------|-------------|---------|---------------------|
| Gemini API | Direct API call (Google AI Studio) | HTTP 5xx / quota exhausted | Store signal; retry queue; show "AI processing delayed" | Citizen signal stored; gap/priority from pre-existing data still works |
| BigQuery | Managed queries via Python client | Service unavailable | Return cached/pre-generated reports (GCS backup) | Citizen submission still works; dashboard shows cached state |
| Cloud Run (backend) | Cloud Run hosted FastAPI | Container restart / OOM | Cloud Run auto-restarts; requests queued briefly | If restart takes >60s: frontend shows API unavailable |
| Cloud Run (frontend) | Cloud Run hosted Next.js | Container restart | Cloud Run auto-restarts | Backend still accepts signals |
| Firebase Auth | Google OAuth flow | Auth service unavailable | Policymaker cannot log in | Citizen portal stays fully open (no auth required) |
| Google Maps Platform | JS Maps API + Geocoding | API unavailable or quota | Fall back to tabular hotspot list (always rendered in parallel) | Full intelligence reports still viewable; no map pins |
| Cloud Storage (audio) | GCS direct upload | Unavailable | Prompt text-only fallback immediately; don't attempt GCS | Voice submission fails gracefully; text works |
| Cloud Storage (raw data) | Static CSV snapshots | N/A -- already in BQ | N/A (data already loaded before demo) | N/A |
| Secret Manager | Runtime secret fetch | Unavailable at startup | Fail fast with clear error; redeploy with secrets pre-loaded | Service cannot start; pre-load critical secrets as env vars as last resort |
| LGD NAPIX Live API | NOT USED in MVP | N/A | Static CSV snapshot loaded in BQ | Fully operational -- no live dependency |
| JJM Live Dashboard | NOT USED in MVP | N/A | Static snapshot in BQ | Fully operational -- no live dependency |
| Mission Antyodaya Portal | NOT USED in MVP | N/A | Static snapshot in BQ | Fully operational -- no live dependency |
| APSAC WMS | NOT USED in MVP | N/A | N/A (excluded from critical path) | N/A |
| e-GramSwaraj | NOT USED in MVP | N/A | N/A (excluded from critical path) | N/A |

---

## Risk Register

### R-001: LGD Name Normalization Failures
- **Probability:** MEDIUM
- **Impact:** HIGH (geography unresolved means no gap calculation)
- **Description:** JJM village names may not match LGD names exactly, especially for newly formed AP districts.
- **Mitigation:** Pre-build `lgd_historical_mapping` table; implement fuzzy matching with confidence threshold; all unresolved geographies stored and exposed (not silently dropped).
- **Fallback:** Store signal as `resolution_status = UNRESOLVED`; flag in dashboard; allow manual review.

### R-002: Gemini Structured Output Schema Mismatch
- **Probability:** LOW (response_schema enforces it)
- **Impact:** MEDIUM (extraction fails for that signal)
- **Description:** Gemini returns JSON that fails Pydantic validation despite response_schema.
- **Mitigation:** Retry once with simplified prompt; log schema version; strict `model_validate_json()` call.
- **Fallback:** Store signal as `extraction_status = FAILED`; notify admin; allow text resubmission.

### R-003: JJM Data Quality Issues
- **Probability:** MEDIUM
- **Impact:** MEDIUM (gap calculation uses partial data)
- **Description:** JJM extract may have missing village-level records or misaligned column names.
- **Mitigation:** Write defensive ingestion scripts with schema validation; set `evidence_quality = PARTIAL` or `MISSING` for affected records.
- **Fallback:** Fall back to district-level JJM data when village data is absent.

### R-004: AP 2022 District Reorganization Join Failures
- **Probability:** MEDIUM-HIGH (known structural issue in research)
- **Impact:** HIGH (affects all AP geography joins)
- **Description:** Pre-2022 JJM data uses old 13-district names; post-2022 LGD uses 26 districts.
- **Mitigation:** Manually create `lgd_historical_mapping` table mapping old district names to new LGD codes; test on Day 1.
- **Fallback:** For unmapped districts, flag as `REQUIRES_MANUAL_REVIEW` and exclude from automated priority calculation.

### R-005: Gemini Audio/Voice Failures for Indian Languages
- **Probability:** MEDIUM
- **Impact:** MEDIUM (voice feature affected; text still works)
- **Description:** Gemini 2.0 Flash may have lower accuracy for Telugu, Kannada, or regional dialects via audio.
- **Mitigation:** Test Telugu audio on Day 2; have English voice as fallback; text submission always available.
- **Fallback:** Prompt user to resubmit as text if audio extraction confidence is below threshold.

### R-006: BigQuery Query Latency on Complex Aggregations
- **Probability:** LOW
- **Impact:** LOW (demo slower; not broken)
- **Description:** Complex JOINs across large LGD table may be slow without optimization.
- **Mitigation:** Use partitioned tables (by date); add CLUSTER BY lgd_district_code on evidence tables; pre-compute hotspot aggregations on ingestion.
- **Fallback:** Add response caching layer (in-memory LRU cache in FastAPI) for hotspot and report queries.

### R-007: Gemini API Key Quota Exhaustion During Demo
- **Probability:** LOW
- **Impact:** CRITICAL for demo
- **Description:** Live demo with high query volume may exhaust free tier quota.
- **Mitigation:** Monitor usage; switch to pre-generated demo fixtures if approaching limit.
- **Fallback:** Demo mode URL parameter serves pre-generated Intelligence Reports without live API calls.

### R-008: Cloud Run Cold Start Delays
- **Probability:** LOW-MEDIUM
- **Impact:** LOW (first request slow; subsequent fast)
- **Description:** Scale-to-zero means first request after idle period has 2-5s cold start.
- **Mitigation:** Send "warm-up" request before demo; Cloud Run min-instances=1 for demo day.
- **Fallback:** Brief delay tolerated; not a functional failure.

### R-009: Firebase Auth OAuth Redirect Configuration
- **Probability:** LOW
- **Impact:** MEDIUM (policymaker cannot log in)
- **Description:** Firebase authorized domains must include the Cloud Run URL exactly.
- **Mitigation:** Configure on Day 1; test before P3 UX work begins.
- **Fallback:** Hard-code a policymaker demo account with pre-generated session token for demo (not production-safe).

### R-010: Maps API District Polygon Availability
- **Probability:** MEDIUM
- **Impact:** LOW (pins still work; polygons are enhancement)
- **Description:** LGD district boundaries may not be available as preprocessed GeoJSON.
- **Mitigation:** Use Google Maps Geocoding to get district centroid lat/lng for pin placement; no polygon needed for MVP.
- **Fallback:** Manual lat/lng for pilot districts (West Godavari, YSR Kadapa) hardcoded as demo fallback.

### R-011: Synthetic Data Leaking into Evidence Calculations
- **Probability:** LOW (with proper flag enforcement)
- **Impact:** CRITICAL (evidence integrity failure)
- **Description:** Synthetic signals accidentally included in official demand count.
- **Mitigation:** `is_synthetic` flag enforced at schema level; all aggregations default to `WHERE is_synthetic = FALSE`; separate `synthetic_demand_count` field in priority table.
- **Fallback:** N/A -- this is a must-prevent scenario.

### R-012: Government Data Portal Unavailable During Live Data Collection
- **Probability:** MEDIUM (known from research)
- **Impact:** NONE for MVP (static snapshots pre-loaded)
- **Description:** JJM/LGD portals go down during the project window.
- **Mitigation:** Download and store all needed data by end of Day 1.
- **Fallback:** Data already in BigQuery; portal downtime is irrelevant after P0.

---

## Demo Reliability Plan

For the hackathon demo specifically:

1. **Pre-generate 3-5 Intelligence Reports** stored in BQ; display without live Gemini call
2. **Demo mode flag** (`?demo=true`) loads fixture data
3. **Min instances = 1** on Cloud Run for demo day (no cold start)
4. **Warm-up script** runs 5 minutes before demo to ensure services active
5. **Backup video** of a working demo session in case live demo fails
6. **Two browser tabs open**: one showing citizen portal, one showing policymaker dashboard

---

*Architecture V1 -- 2026-09-24*
