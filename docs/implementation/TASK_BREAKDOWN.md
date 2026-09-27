# Task Breakdown & Six-Day Execution Plan

> Civic Demand Intelligence & Planning Platform
> Status: **READY FOR ENGINEERING**

This document breaks down the implementation blueprint into bounded, testable, agent-friendly tasks organized into a strict 6-day sprint.

## Day 1: P0 Foundation & Data Gate (CRITICAL PATH)

### Task 1.1: GCP Infrastructure & BigQuery DDL
- **Objective:** Provision `civic_intelligence` dataset, GCS buckets, and apply all final DDL schemas.
- **Dependency:** None
- **Artifact:** BQ tables created; Terraform/scripts merged.
- **Validation:** Schema matches `data-architecture.md` (no materialized views).
- **Status:** CRITICAL

### Task 1.2: LGD & JJM Data Ingestion
- **Objective:** Ingest AP LGD spine and JJM water data for pilot districts. Create `geography_boundary_events` rows.
- **Dependency:** Task 1.1
- **Artifact:** Populated `lgd_*` and `evidence_jjm_*` tables.
- **Validation:** BQ tables contain records.
- **Status:** CRITICAL

### Task 1.3: Data Readiness Gate
- **Objective:** Run deterministic match scripts to verify join strategy.
- **Dependency:** Task 1.2
- **Artifact:** Validation report.
- **Validation:** Pass criteria defined in `DATA_READINESS_GATE.md` (>90% match).
- **Status:** CRITICAL

## Day 2: P1 Vertical Slice - Signal to Score (CRITICAL PATH)

### Task 2.1: Gemini Extraction Integration
- **Objective:** Implement `POST /api/signals/extract` calling Gemini with `CivicNeedExtraction` schema.
- **Dependency:** Task 1.1
- **Artifact:** Python service module for Gemini calls.
- **Validation:** Input synthetic text -> receives valid JSON schema back.
- **Status:** CRITICAL

### Task 2.2: Backend Geography Resolution
- **Objective:** Implement fuzzy matching logic from extracted location to `geography_id`.
- **Dependency:** Task 1.3
- **Artifact:** Python resolution module.
- **Validation:** "palakol" resolves to correct LGD village ID.
- **Status:** CRITICAL

### Task 2.3: Deterministic Scoring Engine & Ledger
- **Objective:** Implement gap calculation, priority formula (V1.0.0), and ledger writes.
- **Dependency:** Task 2.2
- **Artifact:** Backend gap and priority calculation services.
- **Validation:** Known inputs produce mathematically exact expected scores. Ledger writes succeed.
- **Status:** CRITICAL

## Day 3: P2 Analytics & Backend API (CRITICAL PATH)

### Task 3.1: Precomputed Snapshot Generator
- **Objective:** Implement SQL job/endpoint to generate `snapshot_hotspot_summary` and other snapshot tables from raw assessments.
- **Dependency:** Task 2.3
- **Artifact:** Refresh endpoint `POST /api/admin/refresh-snapshots` or BQ Scheduled Query.
- **Validation:** Snapshot tables populate with aggregated data.
- **Status:** CRITICAL

### Task 3.2: Policymaker Dashboard API
- **Objective:** Implement read-only endpoints for the frontend (hotspots, report details).
- **Dependency:** Task 3.1
- **Artifact:** FastAPI routes (`/api/dashboard/hotspots`, `/api/dashboard/reports/{id}`).
- **Validation:** Endpoints return valid JSON matching frontend expectations.
- **Status:** CRITICAL

## Day 4: P3 Frontend & Copilot (CRITICAL PATH)

### Task 4.1: Policymaker Dashboard UI
- **Objective:** Build Next.js dashboard with Hotspot List and basic Map visualization (using precomputed centroids).
- **Dependency:** Task 3.2
- **Artifact:** Deployed Next.js application.
- **Validation:** Dashboard loads hotspot list from backend.
- **Status:** CRITICAL

### Task 4.2: Planning Copilot Integration
- **Objective:** Implement Copilot chat UI and backend tool execution allowlist.
- **Dependency:** Task 4.1
- **Artifact:** Copilot tool registry and chat endpoint.
- **Validation:** Asking "What is the JJM status here?" correctly triggers `get_jjm_scheme_status` tool and returns grounded answer.
- **Status:** CRITICAL

## Day 5: P4 Voice & Demo Hardening (MIXED)

### Task 5.1: Multimodal Voice Extraction
- **Objective:** Connect citizen voice upload to Gemini audio extraction.
- **Dependency:** Task 2.1
- **Artifact:** Audio handling route and GCS upload logic.
- **Validation:** Uploading .wav file creates valid civic need record.
- **Status:** SHOULD (Fallback to text if blocks)

### Task 5.2: GCP STT Fallback (Optional for Demo)
- **Objective:** Implement STT fallback if Gemini audio fails.
- **Dependency:** Task 5.1
- **Artifact:** STT integration module.
- **Validation:** Forced Gemini failure routes to STT and succeeds.
- **Status:** OPTIONAL (Nice to have for robustness)

### Task 5.3: Security & Auth Hardening
- **Objective:** Apply Firebase Auth guards, rate limiting, and input sanitization.
- **Dependency:** Task 4.1
- **Artifact:** Auth middleware.
- **Validation:** Unauthenticated access to dashboard API returns 401.
- **Status:** CRITICAL

## Day 6: P5 Submission & Rehearsal (CRITICAL PATH)

### Task 6.1: Demo Fixture Seeding
- **Objective:** Load specific synthetic signals to guarantee an impressive, stable state for live judging.
- **Dependency:** Task 3.1
- **Artifact:** Database seeded with demo state.
- **Validation:** UI looks perfect upon fresh load.
- **Status:** CRITICAL

### Task 6.2: End-to-End Rehearsal
- **Objective:** Run the full `DEMO_EXECUTION_FLOW.md`.
- **Dependency:** All Critical Tasks
- **Artifact:** Polished pitch and demo video.
- **Validation:** No errors during live run.
- **Status:** CRITICAL

---
*Implementation Plan - Task Breakdown*
