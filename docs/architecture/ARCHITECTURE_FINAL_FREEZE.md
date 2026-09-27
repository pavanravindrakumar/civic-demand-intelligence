# Architecture Final Freeze

> Civic Demand Intelligence & Planning Platform
> Version: FINAL (V1.1 + Google Validation Reconciliation)
> Date: 2026-09-24
> Status: **FROZEN FOR IMPLEMENTATION**

---

## FREEZE DECLARATION

This document represents the authoritative, internally consistent architecture of the Civic Demand Intelligence & Planning Platform. All prior draft documents (V1, V1.1, adversarial review, Google validation) are superseded by the resolutions recorded here.

**No architecture decision may be changed after this document is accepted without a new ADR.**

---

## 1. PRODUCT DEFINITION (LOCKED)

The platform is an **intelligence layer** that transforms citizen development signals into evidence-backed, deterministic priority recommendations for policymakers.

**Core transformation chain:**
```
Citizen Signals
  → Civic Need Discovery
  → Administrative Geography Resolution (versioned LGD)
  → Official Evidence (JJM snapshot)
  → Reported Household Tap-Connection Gap (deterministic)
  → Validated Citizen Demand (deduplicated, bounded)
  → Deterministic Priority Score (versioned policy)
  → Evidence-backed Intelligence Report
  → Policymaker Decision Support
```

**What it is NOT:**
- A grievance portal
- A chatbot or generic Q&A system
- An AI-only scoring system
- A live government data scraper
- A complaint management dashboard

**Core principle:**
> AI interprets. Deterministic systems calculate. Evidence Ledger preserves provenance. Humans make final policy decisions.

---

## 2. LOCKED TECHNOLOGY STACK

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend API | FastAPI (Python 3.11) | Async support; native Pydantic; BigQuery client integration |
| Frontend | Next.js 14 (App Router) | SSR for policymaker dashboard; React ecosystem |
| AI Model | Configurable via `GEMINI_MODEL` env var | Models evolve; do not hardcode |
| Current model candidate | `gemini-3.8-flash` | Flash tier: multimodal, structured output, function calling |
| Analytical backbone | BigQuery (`civic_intelligence` dataset) | Serverless; scales to full India; zero ops |
| Dashboard analytics | **Precomputed analytical snapshot tables** (NOT Materialized Views) | BQ Materialized Views have SQL restrictions; precomputed tables have none |
| Object storage | Google Cloud Storage | Raw snapshots + ephemeral audio |
| Auth | Firebase Authentication (Google OAuth) | Fastest secure auth for 6-day MVP |
| Secrets | Secret Manager | Best practice; Cloud Run native integration |
| Maps | Google Maps JS API (optional, non-critical) | Client-side pin rendering; precomputed centroids |
| Voice primary | Gemini multimodal audio | Single API call; no separate STT pipeline |
| Voice fallback | Google Cloud Speech-to-Text (`te-IN`, `hi-IN`) | Synchronous API; <1 min audio |
| Deployment | Cloud Run (2 services) | Stateless; scale-to-zero; no Kubernetes |
| Region | `asia-south1` (Mumbai) | Latency for India; architecture decision, not legal requirement |

---

## 3. FROZEN AI / DETERMINISTIC BOUNDARY

This boundary is the most important architectural invariant. It MUST NOT be violated during implementation.

| Task | Assigned To | Mechanism |
|------|------------|-----------|
| Multilingual signal understanding | Gemini (`GEMINI_MODEL`) | Multimodal audio or text prompt |
| Civic need classification | Gemini | Structured output with allowlisted `need_type` enum |
| Location expression extraction | Gemini | Returns citizen's own words — never an LGD code |
| Urgency signal detection | Gemini | Tone/sentiment classification |
| LGD code resolution | Backend code only | Fuzzy matching + versioned mapping tables |
| Gap arithmetic | Backend code only | `gap_units = total_households - fhtc_households` |
| Priority score calculation | Backend code only | Deterministic versioned formula |
| Conflict detection | Backend code only | Comparing specific field values |
| Demand deduplication | Backend code only | Idempotency key + session-based grouping |
| Provenance recording | Backend code only | Append-only ledger |
| Copilot narrative | Gemini | Grounded explanation of pre-calculated results from tools |
| Copilot tool execution | Backend code only | Read-only BQ queries; never arbitrary SQL |

---

## 4. FROZEN GEOGRAPHY MODEL

### 4.1 Core Model

LGD is the canonical administrative identity mapping target. The model is **versioned** to handle evolving administrative boundaries.

```
Every administrative entity has:
  geography_id       : Internal stable UUID (never changes even if LGD reorganizes)
  lgd_code           : Current LGD numeric code for this version
  lgd_version        : Version snapshot reference (e.g. "LGD-2025-01")
  source_native_id   : The identifier as found in the source data (string)
  source_native_name : The name as found in the source data (string)
  resolution_status  : CONFIRMED | PROBABLE | UNRESOLVED
  resolution_conf    : 0.0 – 1.0
```

### 4.2 Boundary Evolution Policy

Administrative boundaries evolve. The architecture handles this generically:

- A `geography_versions` table records each known LGD snapshot release
- A `geography_boundary_events` table records splits, merges, renames with `effective_date`
- Source data is reconciled against the appropriate geography version (`data_as_of` vs `effective_date`)
- AP 2022 reorganization (13→26 districts) and the December 2025 reorganization (26→28 districts) are both handled as events in this table — not as special-case code

**There is no hardcoded AP-specific reconciliation path.** The reconciliation logic is generic.

### 4.3 Coordinates

Precomputed representative centroid points (lat/lng) for each canonical geography entity are stored in the `lgd_districts` and `lgd_villages` tables as `centroid_lat` / `centroid_lng` columns.

These are calculated once during the LGD ingestion pipeline, not at runtime. The Google Maps JS API renders them on the client side. No runtime Geocoding API calls.

---

## 5. FROZEN DEEP SECTOR: WATER / JJM

### 5.1 Locked Terminology

| Use | Approved Term |
|-----|--------------|
| The infrastructure measurement | **Reported Household Tap-Connection Gap** |
| The arithmetic | `gap_units = total_reported_households − reported_fhtc_households` |
| What it measures | Difference between JJM-reported total households and JJM-reported functional tap connections |
| What it does NOT measure | Real-world water deprivation; actual need; physical water availability |
| Evidence qualifier | "As reported in JJM data as of [date]" |

### 5.2 Forbidden Terminology

- ~~"Absolute unmet water demand"~~
- ~~"Water deprivation count"~~
- ~~"Households without water"~~ (JJM counts tap connections, not actual water use)
- ~~"Verified gap"~~ unless a secondary source confirms

### 5.3 Gap Calculation Rule

The gap is calculated **only from JJM evidence**. If `total_households` or `fhtc_households` is null in the JJM evidence record, the gap is `NULL` and `evidence_quality = MISSING`. Gemini never estimates a missing value.

### 5.4 Intelligence Chain

```
CitizenSignal
  → CivicNeedExtraction (Gemini)
  → geography_id resolution (backend, versioned LGD)
  → evidence_jjm_village query (latest snapshot for geography_id)
  → gap_units = total_households - fhtc_households (backend arithmetic)
  → GapAssessment stored (calculation_version = "gap.water.v1.0")
  → PriorityAssessment calculated (priority_policy_version = "v1.0.0")
  → IntelligenceReport assembled
  → EvidenceLedger entries written (one per pipeline step)
```

---

## 6. FROZEN PRIORITY ENGINE

### 6.1 Model

Priority is a **deterministic, versioned, configurable policy calculation**. It is not a heuristic and is not generated by AI.

**Current version: `priority_policy_v1.0.0`**

**Factors and weights:**

| Factor | Weight | Input | Normalization |
|--------|--------|-------|---------------|
| Gap Severity | 0.40 | `gap_percentage` (0.0–1.0) | Direct (already 0–1) |
| Population Impact | 0.20 | `gap_units × avg_household_size` | Saturate at 500,000 individuals |
| Validated Citizen Demand | 0.25 | `organic_deduplicated_signal_count` | Saturate at `demand_saturation_cap` config |
| Urgency / Essentiality | 0.05 | `urgency_signal_score` (0.0–1.0) | Derived from Gemini urgency field distribution |
| Evidence Quality | 0.10 | `quality_multiplier` | See table below |

**Evidence quality multipliers:**

| Quality State | Multiplier |
|--------------|-----------|
| AVAILABLE | 1.00 |
| PARTIAL | 0.70 |
| LOW_CONFIDENCE | 0.60 |
| CONFLICTING | 0.50 |
| MISSING | 0.20 |

**Formula:**
```
score = (0.40 × gap_severity)
      + (0.20 × population_impact_normalized)
      + (0.25 × demand_normalized)
      + (0.05 × urgency_normalized)
      + (0.10 × quality_multiplier)

score = clamp(score, 0.0, 1.0)
```

### 6.2 Demand Anti-Manipulation

Citizen demand is the only factor that can be artificially inflated. The following controls are mandatory:

| Control | Mechanism |
|---------|----------|
| Idempotency | `idempotency_key = hash(session_id + text_fingerprint)` |
| Deduplication | Signals with same `idempotency_key` are collapsed to 1 |
| Rate limiting | 5 signals per IP per hour; 20 per IP per day |
| Session grouping | Multiple signals from same session count as 1 civic need signal |
| Demand saturation | `demand_normalized = min(count / demand_saturation_cap, 1.0)` |
| Saturation cap | Default: `demand_saturation_cap = 500` (configurable per deployment) |
| Synthetic exclusion | `organic_deduplicated_signal_count` never includes `is_synthetic = TRUE` signals |

**Key invariant:** 500 synthetic signals + 1 real signal = demand contribution of 1 (organic). Synthetic signals are visible in the UI with counts shown separately, but cannot change the priority score.

### 6.3 Versioning

Every `PriorityAssessment` record stores:
- `priority_policy_version` (e.g. `"v1.0.0"`)
- All factor weights as stored columns (not implicit)
- All factor values as stored columns
- All factor contributions as stored columns
- `demand_saturation_cap` value used
- `calculation_version` (e.g. `"priority.v1.0"`)
- `data_as_of` for each evidence source used

This makes every score independently reconstructable from the record alone.

---

## 7. FROZEN EVIDENCE LEDGER

The Evidence Ledger is the platform's trust foundation. It is append-only.

Every `IntelligenceReport` has a chain of `EvidenceLedgerEntry` records, one per pipeline step:

| Step | `step_type` | Key Fields |
|------|-------------|-----------|
| 1 | `SIGNAL_RECEIVED` | `signal_id`, `is_synthetic`, `source` |
| 2 | `NEED_EXTRACTED` | `civic_need_id`, `need_type`, `extraction_model`, `model_version` |
| 3 | `GEOGRAPHY_RESOLVED` | `geography_id`, `lgd_code`, `lgd_version`, `resolution_status`, `resolution_confidence` |
| 4 | `EVIDENCE_QUERIED` | `evidence_id`, `source = JJM`, `data_as_of`, `snapshot_ref` |
| 5 | `GAP_CALCULATED` | `gap_id`, `gap_units`, `gap_percentage`, `calculation_version`, `evidence_quality` |
| 6 | `PRIORITY_CALCULATED` | `priority_id`, `priority_score`, `priority_tier`, `priority_policy_version` |
| 7 | `CONFLICT_DETECTED` (if any) | `conflict_id`, `conflict_type`, `sources_compared` |
| 8 | `REPORT_GENERATED` | `report_id`, `report_schema_version`, `synthetic_fraction` |

Each entry also stores: `assumptions[]`, `data_quality`, `processing_version`.

---

## 8. FROZEN ANALYTICAL SNAPSHOT STRATEGY (replaces Materialized Views)

**Decision:** BigQuery Materialized Views are **NOT used** in the MVP.

**Reason:** BQ Materialized Views have strict limitations on supported SQL patterns (no OUTER JOINs, no window functions in incremental mode, restricted aggregation functions). These restrictions make them unreliable for complex intelligence aggregations and would require significant debugging time during a 6-day sprint.

**Replacement:** Precomputed Analytical Snapshot Tables.

### 8.1 Pattern

```
Trigger: Data ingestion or signal processing completes
  → Backend calls refresh job (or BQ Scheduled Query)
  → Job runs unrestricted SQL aggregation
  → Result overwrites snapshot table (INSERT OVERWRITE)
  → Dashboard reads from snapshot table (low latency)
```

### 8.2 Snapshot Tables

| Snapshot Table | Refresh Trigger | Latency Impact |
|----------------|----------------|----------------|
| `snapshot_hotspot_summary` | After each batch of signals processed OR hourly | Dashboard load: sub-second read |
| `snapshot_district_intelligence` | After each new report generated | Report list: sub-second read |
| `snapshot_evidence_quality_index` | Daily (ingestion pipeline) | Evidence panel: sub-second read |

### 8.3 Refresh Mechanism (MVP)

**Preferred:** A `POST /api/admin/refresh-snapshots` endpoint on the backend that runs SQL queries to overwrite the three snapshot tables. Called automatically after signal batches and after data ingestion.

**Alternative:** BigQuery Scheduled Query (if SQL is sufficient without joins).

**No external orchestration tool** (no Cloud Composer, no Dataform) required for the MVP.

### 8.4 Honest Latency Statement

> "Precomputed analytical snapshots minimize interactive query work. Actual dashboard latency is empirically benchmarked against live deployment. Stale data is labeled with the snapshot generation timestamp."

---

## 9. FROZEN AUDIO ARCHITECTURE

### 9.1 Primary Path: Gemini Multimodal Audio

```
Citizen audio (WAV/MP3/OGG, ≤5MB, ≤60s)
  → Backend stores in GCS (civic-audio bucket, TTL=24h)
  → GCS URI passed to Gemini: Part.from_uri(gcs_uri, mime_type)
  → Gemini extracts CivicNeedExtraction directly from audio
  → Pydantic validates output
  → Audio GCS record deleted after extraction (or at 24h TTL)
```

### 9.2 Fallback Path: Google Cloud Speech-to-Text

Triggered when Gemini audio extraction fails (Pydantic validation fails twice):

```
Citizen audio
  → Google Cloud STT synchronous API
  → Parameters: language_code=detected_language, model="latest_long"
  → Returns: transcript string
  → Transcript passed to Gemini as TEXT input (same CivicNeedExtraction schema)
  → Pydantic validates output
```

**Key design constraint:** The `CivicNeedExtraction` Pydantic schema is **identical** for both paths. The extraction interface is path-agnostic. Only the backend routing changes.

### 9.3 Supported Languages (Pilot)

| Language | BCP-47 | Gemini Audio | GCP STT |
|----------|--------|-------------|---------|
| Telugu | `te-IN` | Verify on Day 1 | Supported |
| Hindi | `hi-IN` | Supported | Supported |
| English | `en-IN` | Supported | Supported |

If both paths fail for a signal: UI prompts "Could not process audio. Please type your request instead." Signal stored as `extraction_status = FAILED`.

---

## 10. FROZEN COPILOT ARCHITECTURE

### 10.1 Security Model

```
Policymaker question (auth required)
  → Backend input validation (length, injection check)
  → Gemini: question + system prompt + report context + tool declarations
  → Gemini proposes tool call
  → Backend: allowlist check → argument validation → authorization check
  → Backend: executes read-only BQ query
  → Result validated against output schema
  → If evidence absent: return NO_DATA sentinel (never fabricate)
  → Gemini: generates grounded explanation
  → Backend: output safety check
  → Frontend: displays with [AI EXPLANATION] label
```

### 10.2 Frozen Tool List (MVP)

| Tool | Data Source | Returns if Missing |
|------|------------|-------------------|
| `get_hotspot_details` | `snapshot_hotspot_summary` | `{data_status: "NO_DATA", message: "..."}` |
| `get_intelligence_report` | `intelligence_reports` | `{data_status: "NO_DATA"}` |
| `explain_priority_score` | `priority_assessments` | `{data_status: "NO_DATA"}` |
| `show_evidence_conflict` | `evidence_conflicts` | `{data_status: "NO_DATA"}` |
| `compare_policy_weights` | Computed in-memory from `gap_assessments` | `{data_status: "NO_DATA"}` |
| `get_jjm_scheme_status` | `evidence_jjm_village` | `{data_status: "NO_DATA"}` |

**Removed from all tool lists and contracts:** `list_overlapping_interventions` (no intervention data in MVP).

### 10.3 Invariants

- No tool accepts freeform SQL
- No tool writes to any table
- All tool inputs are Pydantic-validated
- Tool names are validated against a hard-coded allowlist before any execution
- Rate limit: 20 Copilot queries per policymaker per hour

---

## 11. FROZEN UX ARCHITECTURE

### 11.1 Policymaker Dashboard: Map + Hotspot List Split

The dashboard presents **two simultaneously visible panels**:

| Panel | Content | Fallback if fails |
|-------|---------|-------------------|
| **Map** (left/top) | District pins colored by priority tier; from precomputed centroids | Hidden; hotspot list remains |
| **Hotspot List** (right/bottom) | Ranked table of districts/needs by priority score | Always rendered; never hidden |

The hotspot list is the **operationally reliable primary interface**. The map is an enrichment layer. If the Maps JS API fails, the dashboard degrades gracefully to list-only — this is explicitly handled in the frontend.

### 11.2 Trust Model (Mandatory UI States)

Every piece of data displayed must carry one of these states:

| State | Badge | Color |
|-------|-------|-------|
| OFFICIAL EVIDENCE | None (default) | Neutral |
| AI INTERPRETATION | `[AI]` | Blue |
| SYNTHETIC | `[SYNTHETIC]` | Purple |
| MISSING | `[NO DATA]` | Grey |
| PARTIAL | `[PARTIAL]` | Yellow |
| CONFLICTING | `[CONFLICTING]` | Orange |
| HISTORICAL | `[HISTORICAL — {year}]` | Amber |

The distinction between **AI Interpretation** and **Deterministic Official Evidence** must be visually clear at all times.

### 11.3 Citizen Portal

Mobile-first. Single form. Multilingual voice/text toggle.

- No authentication required for signal submission
- Language hint selector (Hindi, Telugu, English + auto-detect)
- Audio: record in browser or upload file (WAV/MP3/OGG, ≤5MB, ≤60s)
- Immediate feedback: `signal_id` reference number + "Your report has been received"
- No PII collected (no name, phone, email)

---

## 12. FROZEN SECURITY MODEL

### 12.1 PII Minimization

- No name, phone, or email collected from citizens
- Audio stored ephemerally (GCS TTL = 24h; deleted after extraction where possible)
- `submitter_pseudonym` is an optional session UUID, not linked to any identity

### 12.2 Input Security

| Attack Vector | Defense |
|--------------|---------|
| Prompt injection via citizen text | Sanitize input (HTML strip, length limit) BEFORE any prompt concatenation; use API message roles not string concat |
| Prompt injection via audio content | Gemini structured output schema enforces JSON-only response; no free-text path |
| LLM hallucinated statistics in Copilot | All Copilot answers grounded via tool results; system prompt explicitly prohibits invention |
| Schema bypass | Pydantic validation on every Gemini output; extraction stored as `FAILED` on validation error |

### 12.3 Synthetic Data Invariant

- `is_synthetic` is a `NOT NULL` column with no server-side default
- Setting `is_synthetic = FALSE` on a signal that was created synthetic is a bug (enforced by service layer)
- Synthetic signals are excluded from `organic_deduplicated_signal_count` by query predicate, not by application logic toggle

### 12.4 IAM

| Service Account | Permissions |
|----------------|-------------|
| `civic-backend-sa` | `bigquery.dataEditor` (intelligence tables only), `bigquery.dataViewer` (evidence tables), `bigquery.jobUser`, `storage.objectUser` (audio bucket), `secretmanager.secretAccessor` |
| `ingest-sa` | `bigquery.dataEditor` (all tables), `storage.objectUser` (raw-data bucket) |

No service account has `bigquery.admin` or `storage.admin` privileges.

### 12.5 Firebase API Key Restriction

The Firebase web config API key exposed in the Next.js frontend MUST be restricted in GCP Console to allow only the Firebase Authentication API. Not a broad GCP API key.

---

## 13. FROZEN DEPLOYMENT

### 13.1 Services

| Service | Runtime | CPU | Memory | Min Instances | Max Instances |
|---------|---------|-----|--------|---------------|---------------|
| `civic-backend` | Python 3.11 / FastAPI | 1 vCPU | 512MB | 0 (1 during demo window) | 3 |
| `civic-frontend` | Node 20 / Next.js | 1 vCPU | 512MB | 0 (1 during demo window) | 3 |

**During live judging:** Set `--min-instances=1` on both services to eliminate cold starts.

### 13.2 GEMINI_MODEL Configuration

```bash
# In civic-backend Cloud Run environment variables:
GEMINI_MODEL=gemini-3.8-flash   # configurable; do not hardcode in application code
```

The model is loaded at service startup from this environment variable. Changing the model requires only a Cloud Run environment variable update and service redeploy, not a code change.

### 13.3 Demo Reliability

A `GET /api/demo/reports` endpoint returns pre-generated fixture Intelligence Reports that do not require live Gemini or BigQuery calls. The frontend activates fixture mode when `?demo=true` is present in the URL.

**Demo mode is clearly labeled in the UI:** `[DEMO MODE — Pre-loaded Intelligence Reports]`

---

## 14. FROZEN SIX-DAY IMPLEMENTATION PLAN

The **P1 vertical slice is the only non-negotiable deliverable.** Everything else is enhancement.

### P1 Vertical Slice (Cannot be cut):
```
Synthetic text signal submitted via API form
  → Gemini extracts CivicNeedExtraction (structured JSON)
  → Backend resolves geography to versioned LGD
  → Backend queries JJM evidence from BigQuery
  → Backend calculates Reported Household Tap-Connection Gap
  → Backend calculates Priority Score (deterministic formula)
  → IntelligenceReport assembled and stored in BigQuery
  → EvidenceLedger written (full provenance chain)
  → Report rendered in policymaker dashboard
  → Report shows: gap, priority score with factor breakdown, evidence quality, data source
```

### Phase Order:

| Phase | Day | Goal | Exit Criterion |
|-------|-----|------|----------------|
| P0 | 1 | GCP setup, tables, data ingested, services deployed | `GET /health` returns 200; BQ tables populated |
| P1 | 2–3 | One complete vertical slice working | Synthetic signal → full Intelligence Report in browser |
| P2 | 3–4 | Multiple signals, hotspot aggregation, conflict detection | Hotspot list shows; YSR Kadapa conflict visible |
| P3 | 4–5 | Map+List UX, Copilot, voice input | Policymaker can traverse full workflow in one session |
| P4 | 5–6 | Security hardening, demo prep, precomputed snapshots | Smoke tests pass; demo fixtures verified |
| P5 | 6 | Submission | Video + pitch + live URL submitted |

### Explicit Cut Decisions:

| Feature | Status | Trigger to Cut |
|---------|--------|----------------|
| Voice input (Gemini audio) | SHOULD | If P1 slips past Day 3 |
| Google Maps pins | SHOULD | If Maps API has configuration issues |
| Copilot | SHOULD | If P3 UX slips |
| Mission Antyodaya enrichment | OPTIONAL | If ingestion is complex |
| Census 2011 population | OPTIONAL | If Census join adds >2h of work |
| Evidence conflicts screen | SHOULD | If P3 slips |
| Priority weight admin UI | DEFERRED | Not for MVP; weights hardcoded in config |
| e-GramSwaraj interventions | DEFERRED | No data available |
| PMGSY / Roads sector | DEFERRED | Requires spatial routing |
| Country adapters beyond India | DEFERRED | Interface documented; not implemented |

---

## 15. CONTRADICTION AUDIT AND RESOLUTIONS

The following contradictions were identified across architecture documents and are hereby resolved:

| # | Contradiction | Resolution |
|---|--------------|------------|
| 1 | `ai-architecture.md` hardcodes `gemini-2.0-flash` throughout including in code examples | **Resolved:** All references to specific model names in code examples are replaced with `os.environ["GEMINI_MODEL"]`. The model name is never hardcoded. |
| 2 | `deployment-architecture.md` diagram labels `Gemini 2.0 Flash` specifically | **Resolved:** Diagram label updated to `Gemini API (GEMINI_MODEL)`. |
| 3 | `ARCHITECTURE_MASTER_DIGEST.md` (V1.1) still references "BigQuery Materialized Views" in sections 3, 5, and 13 | **Resolved:** All Materialized View references replaced with "Precomputed Analytical Snapshot Tables" throughout. |
| 4 | `implementation-plan.md` P4 tasks list "Materialized BQ Views" as a hardening task | **Resolved:** P4 task updated to "Precomputed snapshot tables populated and verified." |
| 5 | `ai-architecture.md` still lists `list_overlapping_interventions` in the Copilot tool list and ALLOWLIST Python code | **Resolved:** Tool removed from all tool lists, code examples, and contracts. |
| 6 | `data-architecture.md` Principle 2 states "LGD numeric codes are the universal foreign key" — implies immutability | **Resolved:** Principle reworded to "LGD numeric codes are the canonical administrative identity for the active geography version." The versioning model governs reconciliation. |
| 7 | `data-architecture.md` lgd_historical_mapping table covers only "pre-2022 AP reorganization" by name | **Resolved:** Table renamed to `geography_boundary_events` and made generic to handle any future reorganization. The AP 2022 and AP 2025 events are loaded as rows. |
| 8 | `deployment-architecture.md` Deployment Sequence Step 6 lists Mission Antyodaya ingestion as part of Day 1 P0 | **Resolved:** Mission Antyodaya ingestion removed from Day 1. It is OPTIONAL and belongs in P2/Optional. |
| 9 | `implementation-plan.md` P1 lists "Mission Antyodaya ingestion script" as SHOULD priority | **Resolved:** Mission Antyodaya moved to P2 OPTIONAL. P1 contains only JJM + LGD. |
| 10 | `ai-architecture.md` audio fallback states: "user prompted to re-submit as text" — no formal GCP STT path documented | **Resolved:** Formal GCP STT fallback path documented in ai-architecture.md and in this freeze document (Section 9.2). |
| 11 | `ARCHITECTURE_MASTER_DIGEST.md` (V1.1) assumption 3 states "BigQuery materialized views will keep dashboard load times under 1 second" | **Resolved:** Assumption replaced with "Precomputed analytical snapshot tables are expected to yield sub-second dashboard reads; actual latency empirically benchmarked on live deployment." |
| 12 | `gap_assessments` table column `unmet_households` exists in `evidence_jjm_village` but schema comment says "calculated: total - fhtc" — conflates evidence storage with calculation | **Resolved:** `evidence_jjm_village.unmet_households` is removed. The gap is calculated in `gap_assessments.gap_units` only, so the calculation layer is clearly separated from the evidence layer. |
| 13 | `copilot-tool-contract.md` contains `list_overlapping_interventions` tool definition | **Resolved:** Tool removed from contract document. |
| 14 | `priority_assessments` table schema in V1 has 4 factors (gap, demand, pop, quality) but V1.1 priority engine specifies 5 factors (+ urgency) | **Resolved:** Table schema updated to add `factor_urgency_weight`, `factor_urgency_value`, `factor_urgency_contribution` columns. |

---

## 16. FINAL ARCHITECTURE STATUS

**READY FOR IMPLEMENTATION**

All internal contradictions resolved. All Google-specific claims validated. All locked decisions documented with explicit reasoning. No speculative technologies introduced.

The implementation team may proceed to the P0 Foundation phase.

---

*Architecture FINAL FREEZE — 2026-09-24*
