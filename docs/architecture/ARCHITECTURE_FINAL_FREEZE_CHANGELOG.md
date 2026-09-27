# Architecture Final Freeze Changelog

> Civic Demand Intelligence & Planning Platform
> Date: 2026-09-24
> Scope: All changes applied during the Final Freeze pass (V1.1 → FINAL)

This document records every decision change applied during the final freeze reconciliation. Each entry shows the old decision, the new decision, the reason, and the impact on implementation.

---

## Contradiction Resolutions

| # | Old Decision | New Decision | Reason | Impact on Implementation |
|---|-------------|--------------|--------|--------------------------|
| 1 | Hardcoded `gemini-2.0-flash` throughout `ai-architecture.md` code examples | `os.environ["GEMINI_MODEL"]` everywhere; no hardcoded model name in code | Models evolve; validated candidate is `gemini-3.8-flash` | All backend code must read model name from env var at runtime. CI/CD sets the var. |
| 2 | Deployment diagram labels "Gemini 2.0 Flash" | Diagram label: "Gemini API (GEMINI_MODEL)" | Diagram must match configurable model architecture | One diagram update only |
| 3 | "BigQuery Materialized Views" for dashboard analytics (ARCHITECTURE_MASTER_DIGEST V1.1, sections 3/5/13) | "Precomputed Analytical Snapshot Tables" | Materialized Views have strict SQL restrictions (no OUTER JOINs, no window functions in incremental mode); unreliable for hackathon sprint | Implement 3 snapshot tables (`snapshot_hotspot_summary`, `snapshot_district_intelligence`, `snapshot_evidence_quality_index`). Refresh via backend endpoint after each batch. |
| 4 | P4 hardening task: "Materialized BQ Views" | P4 hardening task: "Precomputed snapshot tables populated and verified" | Consistency with resolution #3 | Rename the implementation task; no structural change |
| 5 | `list_overlapping_interventions` in Copilot tool list, ALLOWLIST code, and contracts | Tool completely removed from MVP | No intervention dataset exists in MVP; demo-breaking to show a tool that always returns MISSING | Remove from: `ai-architecture.md`, `copilot-tool-contract.md`, ALLOWLIST Python dict, `ARCHITECTURE_MASTER_DIGEST.md` |
| 6 | data-architecture.md Principle 2: "LGD numeric codes are the universal foreign key" | "LGD numeric codes are the canonical administrative identity for the **active geography version**" | Previous wording implied immutability; LGD codes change with reorganizations | Add `geography_id` (stable internal UUID) to canonical geography tables as the true stable PK |
| 7 | `lgd_historical_mapping` table (AP-2022-specific) | `geography_boundary_events` table (generic) | AP has undergone 2022 and 2025 reorganizations; more will occur; hardcoding AP-specific logic is wrong | New generic table schema; AP 2022 (13→26) and AP 2025 (26→28) are both loaded as data rows |
| 8 | deployment-architecture.md Day 1 sequence includes Mission Antyodaya ingestion | Mission Antyodaya removed from Day 1 | Mission Antyodaya is OPTIONAL and must not block P0 or P1 | Day 1 ingestion: LGD + JJM only |
| 9 | implementation-plan.md P1 lists Mission Antyodaya ingestion as SHOULD | Moved to P2 OPTIONAL | Mission Antyodaya is supporting enrichment, not core gap data | No priority assessment or gap calculation depends on it |
| 10 | ai-architecture.md audio fallback: "user prompted to re-submit as text" (informal) | Formal GCP STT fallback: audio → STT → transcript → Gemini text path | STT supports Telugu/Hindi; the fallback needs a concrete implementation path, not just a prompt | Two distinct backend code paths share identical `CivicNeedExtraction` output schema |
| 11 | ARCHITECTURE_MASTER_DIGEST assumption 3: "BQ materialized views will keep dashboard load times under 1 second" | "Precomputed analytical snapshot tables are expected to yield sub-second dashboard reads; actual latency empirically benchmarked on live deployment" | Making performance guarantees is intellectually dishonest before empirical testing | Wording updated in digest and all latency claims |
| 12 | `evidence_jjm_village` table has `unmet_households` column ("calculated: total - fhtc") | Column removed from evidence table; calculation lives only in `gap_assessments.gap_units` | Evidence tables should store raw source data; calculations belong in the derived layer | JJM ingestion scripts must NOT write `unmet_households`; the gap calculator reads the evidence and writes to `gap_assessments` |
| 13 | `copilot-tool-contract.md` contains `list_overlapping_interventions` tool definition | Tool definition removed from contract | Consistency with resolution #5 | Contract document updated |
| 14 | `priority_assessments` table has 4 factor columns (gap, demand, pop, quality) | 5 factor columns added: gap, demand, pop, urgency, quality | V1.1 priority engine added Urgency as a factor (weight 0.05); schema was not updated | Add `factor_urgency_weight`, `factor_urgency_value`, `factor_urgency_contribution` columns to `priority_assessments` DDL |

---

## New Decisions (Additions in Final Freeze)

| Decision | Reason | Impact |
|----------|--------|--------|
| `geography_id` stable internal UUID added to all canonical geography tables | LGD codes change; the internal ID never changes even across reorganizations | All FK references to geography in other tables use `geography_id`, not `lgd_*_code` directly |
| `geography_boundary_events` table replaces `lgd_historical_mapping` | Generic boundary event model handles any future reorganization | Migration: AP 2022 + AP 2025 data loaded as rows in this table during P0 |
| `snapshot_hotspot_summary`, `snapshot_district_intelligence`, `snapshot_evidence_quality_index` tables defined | Replaces Materialized Views for dashboard performance | Backend `POST /api/admin/refresh-snapshots` populates these after each processing batch |
| `get_jjm_scheme_status` Copilot tool added | Replaces the removed intervention tool with a tool that has actual MVP data | Tool queries `evidence_jjm_village` for scheme coverage status |
| Audio extraction: `CivicNeedExtraction` schema is **identical** for both Gemini audio and STT text paths | Interface must be path-agnostic for clean fallback implementation | Backend routing logic changes; schema contract does not |
| Demand saturation cap (`demand_saturation_cap`) is a configurable deployment parameter | Prevents the saturation value from being a magic number embedded in code | Stored in a `priority_policy_config` table; loaded at priority calculation time |

---

*Architecture Final Freeze Changelog — 2026-09-24*
