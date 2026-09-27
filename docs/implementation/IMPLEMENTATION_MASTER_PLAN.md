# Implementation Master Plan

> Civic Demand Intelligence & Planning Platform
> Status: **READY FOR ENGINEERING**
> Alignment: Architecture FINAL FREEZE (2026-09-24)

This document is the authoritative implementation blueprint. It translates the frozen architecture into concrete engineering invariants, contracts, and pipelines.

**NO ARCHITECTURAL CHANGES ARE PERMITTED DURING IMPLEMENTATION.** If a blocker arises, a formal ADR is required.

---

## 1. DATA PIPELINE & GEOGRAPHY RESOLUTION

### 1.1 Canonical Geography Resolution Pipeline
The pipeline maps messy citizen input to the versioned LGD spine.

```text
Citizen location expression (e.g., "Palakollu village")
        ↓
1. Normalization (Backend): Lowercase, strip punctuation, remove generic terms ("village", "mandal")
        ↓
2. Candidate Search (Backend / BigQuery): Fuzzy string match against lgd_villages.source_native_name and lgd_districts.source_native_name
        ↓
3. Resolution Status:
   - Exact match (Confidence 1.0) -> CONFIRMED
   - Fuzzy match (Confidence > 0.8) -> PROBABLE
   - Multiple / Low confidence -> UNRESOLVED
        ↓
4. LGD Stable Identifier: Assign the internal `geography_id`
        ↓
5. Validation: Cross-reference with `geography_versions` and `geography_boundary_events` to ensure code is active.
```

**Edge Cases:**
- **Ambiguous village (multiple matches):** Check contextual district/state hints. If unresolved, map to higher level (District).
- **District-only input:** Resolve to District `geography_id`. Village fields remain NULL.
- **Landmark-only / Missing:** `resolution_status = UNRESOLVED`. Cannot calculate gap.
- **Outdated geography:** Backend resolves through `geography_boundary_events` to the current `geography_id`.

### 1.2 Precomputed Snapshot Strategy (Replaces Materialized Views)
Snapshots isolate the dashboard from heavy analytical joins.

**Implementation Mechanism:** BigQuery Scheduled Queries (preferred for simplicity) OR Cloud Run `POST /api/admin/refresh-snapshots` endpoint executing `INSERT OVERWRITE` SQL.

**Snapshot Tables:**
1. `snapshot_hotspot_summary`: `district_id`, `total_gap`, `avg_priority`, `demand_count`, `centroid_lat`, `centroid_lng`. (Refreshed hourly or post-batch).
2. `snapshot_district_intelligence`: Denormalized report summaries for list views.
3. `snapshot_evidence_quality_index`: Aggregated quality scores by district.

*Latency statement: Precomputed analytical snapshots minimize interactive query work; actual latency is measured during implementation.*

---

## 2. SIGNAL PROCESSING & DEMAND ENGINE

Citizen demand is deduplicated and capped to prevent manipulation.

**Processing Pipeline:**
1. **Intake:** Signal received via `POST /api/signals`.
2. **Fingerprinting:** `duplicate_fingerprint = hash(normalized_text + timestamp_hour)`.
3. **Idempotency:** `idempotency_key = hash(session_id + duplicate_fingerprint)`.
4. **Rate Limiting:** IP-based via Redis (if available) or in-memory (5/hour, 20/day per IP).
5. **Deduplication:** Signals with the same `idempotency_key` are collapsed.
6. **Saturation:**
   - Real count: `organic_deduplicated_signal_count` (excludes `is_synthetic = TRUE`).
   - Saturated count: `min(organic_deduplicated_signal_count, demand_saturation_cap)`.
7. **Aggregation:** Eligible for analytical aggregation immediately upon database write.

---

## 3. SCORING IMPLEMENTATION CONTRACT

The numerical priority score is **100% deterministic** and computed in the backend. Gemini NEVER calculates this score.

**Configuration (default `priority_policy_v1.0.0`):**
- `demand_saturation_cap` = 500

| Factor | Weight | Source | Normalization | Bound |
|--------|--------|--------|---------------|-------|
| Gap Severity | 0.40 | `gap_units / total_households` | Direct (0.0 - 1.0) | [0.0, 1.0] |
| Population Impact | 0.20 | `gap_units * avg_size` | `val / 500000` | Max 1.0 |
| Citizen Demand | 0.25 | `organic_dedup_count` | `val / saturation_cap` | Max 1.0 |
| Urgency | 0.05 | Gemini classification | Map enum to [0.0, 1.0] | [0.0, 1.0] |
| Evidence Quality | 0.10 | JJM data state | Enum multiplier | [0.2, 1.0] |

**Quality Multipliers:**
AVAILABLE (1.0), PARTIAL (0.7), LOW_CONFIDENCE (0.6), CONFLICTING (0.5), MISSING (0.2).

**Missing Data Handling:** If JJM `total_households` or `fhtc_households` is NULL -> Gap is NULL -> Score uses `quality_multiplier = 0.2` and `gap_severity = 0.0`.

**Formula:**
`Score = Clamp( (0.40 * Gap) + (0.20 * Pop) + (0.25 * Demand) + (0.05 * Urgency) + (0.10 * Quality), 0.0, 1.0 )`

---

## 4. AI & GEMINI INTEGRATION

**Model:** `GEMINI_MODEL` env var (Target: `gemini-3.8-flash`).

### 4.1 Audio / Voice Extraction
1. **Primary Path:** Citizen audio uploaded -> Backend saves to GCS (TTL 24h) -> Passes `Part.from_uri(gcs_uri)` to Gemini.
2. **Schema:** Pydantic `CivicNeedExtraction` via `response_schema`.
3. **Retry:** If Pydantic validation fails, retry 1x.
4. **Fallback (STT):** If Gemini audio fails 2x, route to Google Cloud Speech-to-Text (`latest_long`). Send resulting text transcript to Gemini.
5. **Failure:** If both fail, `extraction_status = FAILED`.

### 4.2 Security & Bounding
- **Injection:** Sanitize text inputs before passing to Gemini. No string concatenation for prompts (use API message roles).
- **Malformed Response:** Caught by Pydantic. Treated as extraction failure.
- **Tokens/Latency:** Max output tokens = 1024. Low temperature (0.1) for extraction.

---

## 5. COPILOT IMPLEMENTATION

Copilot is **read-only**, backend-authorized, and uses pre-defined tools. No arbitrary SQL.

**Approved Tools:**
1. `get_hotspot_details` (Source: `snapshot_hotspot_summary`)
2. `get_intelligence_report` (Source: `intelligence_reports`)
3. `explain_priority_score` (Source: `priority_assessments`)
4. `get_jjm_scheme_status` (Source: `evidence_jjm_village`) - *Verifies JJM scheme status. Replaces interventions.*
5. `show_evidence_conflict` (Source: `evidence_conflicts`)
6. `compare_policy_weights` (Source: computed in-memory based on `gap_assessments`)

**Execution Contract:**
- `NO_DATA` Behavior: If BQ returns empty, the tool returns a strict `{"data_status": "NO_DATA"}`. Gemini must explain the absence of data, NOT invent numbers.
- Error Behavior: Bubble to UI gracefully. Audit logged.
- Authorization: Checked at the API route level via Firebase Auth token.

---

## 6. EVIDENCE LEDGER

The ledger is append-only. Every report must have traceable provenance.

**Ledger Record Structure (per event):**
- `report_id`
- `step_type` (SIGNAL_RECEIVED, NEED_EXTRACTED, GEOGRAPHY_RESOLVED, EVIDENCE_QUERIED, GAP_CALCULATED, PRIORITY_CALCULATED)
- `geography_version` (e.g., LGD-2025-01)
- `dataset_ids` & `dataset_vintages` (e.g., JJM as of 2025-09-01)
- `synthetic_fraction` (0.0 for pure organic)
- `calculation_version` (e.g., priority.v1.0)
- `missing_data_flags` (boolean array)
- `assumptions` (array of strings)

---

## 7. UX & FRONTEND FLOW

**Minimum Policymaker Flow (Build First):**
1. Login via Firebase Auth.
2. View Dashboard (List + Precomputed Map Pins).
3. Select District Hotspot -> Open Intelligence Report.
4. View Evidence breakdown (Reported Gap + Deterministic Priority + Provenance).
5. Open Copilot -> Ask "What is the JJM status here?" -> See grounded tool response.

**Minimum Citizen Flow (Build Second):**
1. Open mobile web UI.
2. Record Audio OR Type Text.
3. Submit -> See `signal_id` confirmation. No PII collected.

*Map Implementation:* UI renders Google Maps using `centroid_lat` / `centroid_lng` from the snapshot tables. No live geocoding API calls.

---

## 8. DEPLOYMENT CONFIGURATION

**Infrastructure (MVP):**
- Runtime: Cloud Run (2 services: `civic-backend`, `civic-frontend`).
- Database: BigQuery (`civic_intelligence` dataset in `asia-south1`).
- Storage: GCS (`civic-raw-data`, `civic-audio`).
- Auth: Firebase Authentication (Google OAuth).
- Secrets: Secret Manager (`GEMINI_API_KEY`).

**Environment Variables:**
```env
GOOGLE_CLOUD_PROJECT=...
BIGQUERY_DATASET=civic_intelligence
GEMINI_MODEL=gemini-3.8-flash
GEMINI_API_KEY=...
ENVIRONMENT=production
```

**Deployment Sequence:**
1. Terraform/CLI infra setup (BQ, GCS).
2. Data prep & Snapshot seeding.
3. Backend deploy.
4. Frontend deploy.

---
*Status: READY TO BEGIN ENGINEERING.*
