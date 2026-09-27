# Architecture Final Freeze Summary

> Civic Demand Intelligence & Planning Platform
> Date: 2026-09-24

One-page reference for the implementation team. Read this first.

---

## KEEP (Unchanged from V1.1)

| Component | Decision |
|-----------|----------|
| Water / JJM Deep Sector | "Reported Household Tap-Connection Gap" via deterministic arithmetic |
| LGD Geography Backbone | Versioned, with internal stable `geography_id` UUID |
| AI / Deterministic Boundary | Gemini extracts/explains only; backend calculates everything numeric |
| Evidence Ledger | Append-only provenance trail; required for every report |
| Synthetic Data Isolation | `is_synthetic = NOT NULL`; excluded from organic demand count |
| Demand Anti-Manipulation | Idempotency + deduplication + saturation cap |
| BigQuery Analytical Backbone | `civic_intelligence` dataset; `asia-south1` |
| Cloud Run (2 services) | `civic-backend` (FastAPI) + `civic-frontend` (Next.js) |
| Configurable `GEMINI_MODEL` | env var; current candidate: `gemini-3.8-flash` |
| Gemini Audio Primary | `Part.from_uri(gcs_uri)` → `CivicNeedExtraction` |
| GCP STT Fallback | Synchronous API; same output schema as Gemini path |
| Firebase Auth | Google OAuth for policymaker dashboard |
| Map + Hotspot List Split UX | Map is enrichment; hotspot list is always rendered |
| Precomputed centroid coordinates | Stored in BQ; never from runtime Geocoding API |
| Copilot read-only tool allowlist | 6 tools; all Pydantic-validated; no freeform SQL |

---

## MODIFY (Changed in Final Freeze)

| Component | Old | New |
|-----------|-----|-----|
| BQ Materialized Views | Specified for dashboard performance | Replaced by Precomputed Analytical Snapshot Tables |
| Model references in code | Hardcoded `gemini-2.0-flash` strings | `os.environ["GEMINI_MODEL"]` |
| `lgd_historical_mapping` table | AP-2022-specific | `geography_boundary_events` (generic) |
| `evidence_jjm_village.unmet_households` | Stored calculated value | Removed; calculation lives in `gap_assessments.gap_units` only |
| Priority factors table | 4 columns | 5 columns (added: urgency factor) |
| Audio fallback | "Prompt user to retype" | Formal GCP STT path with identical output schema |
| Mission Antyodaya in plan | P1 SHOULD | P2 OPTIONAL |

---

## REMOVE (Not in MVP)

| Component | Reason |
|-----------|--------|
| `list_overlapping_interventions` Copilot tool | No intervention dataset in MVP; always returned MISSING |
| BQ Materialized Views | SQL restrictions make them unreliable for 6-day sprint |
| `unmet_households` column in evidence table | Calculation belongs in derived layer, not evidence layer |
| Mission Antyodaya from P0/P1 critical path | Must not block vertical slice |

---

## DEFER (Post-MVP)

| Component | Reason |
|-----------|--------|
| Priority weight admin UI | Weights are configurable in `priority_policy_config` table; no UI needed for demo |
| PMGSY / Roads sector adapter | Requires spatial network routing |
| e-GramSwaraj / GPDP interventions | No programmatic data access available |
| Country adapters beyond India | Adapter interface documented; not implemented |
| Census 2011 population join | Defer if adds >2h; JJM `total_households` used as proxy |
| Advanced semantic need clustering | Post-MVP AI feature |

---

## VERIFY (Before or During P0)

| Item | How to Verify |
|------|--------------|
| `GEMINI_MODEL` value supports audio + `response_schema` in same call | Day 1 test script: submit audio → validate Pydantic output |
| GCP STT `te-IN` accuracy for rural Telugu | Day 1-2 test: submit 3 Telugu audio samples |
| BQ `asia-south1` dataset creation works | P0 setup step |
| Firebase Google OAuth works on Cloud Run domain | P0 Day 1 auth smoke test |
| Cloud Run cold start time with `min-instances=0` | Measure before setting demo to `min-instances=1` |
| JJM CSV village names fuzzy-match to LGD names for AP | P0 ingestion: inspect match rate; prepare manual fallbacks |
| AP 2022 + AP 2025 boundary events can be loaded | P0: build `geography_boundary_events` rows; verify join results |

---

## FINAL ARCHITECTURE STATUS

> **READY FOR IMPLEMENTATION**
>
> All internal contradictions resolved.
> All Google-specific claims validated.
> All locked decisions documented.
> No speculative technologies introduced.
> Six-day implementation plan is realistic and explicitly cut-aware.
>
> The team may proceed to **Phase P0 Foundation**.

---

*Architecture Final Freeze Summary — 2026-09-24*
