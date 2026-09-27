# ADR-006 through ADR-013

(Stubs -- full rationale in decision-summary.md)

| ADR | Title | See |
|-----|-------|-----|
| ADR-006 | Cloud Run Monorepo Deployment | [0004-static-data-snapshots.md](0004-static-data-snapshots.md) |
| ADR-007 | Pilot Geography: Andhra Pradesh | [decision-summary.md](../architecture/decision-summary.md) |
| ADR-008 | Synthetic Data Isolation Policy | [security-architecture.md](../architecture/security-architecture.md) |
| ADR-009 | Deterministic Priority Score | [gap-priority-contract.md](../data-contract/gap-priority-contract.md) |
| ADR-010 | Tabular-Only Spatial Strategy | [decision-summary.md](../architecture/decision-summary.md) |
| ADR-011 | Gemini Multimodal over Separate STT | [ai-architecture.md](../architecture/ai-architecture.md) |
| ADR-012 | Copilot Security Model | [copilot-tool-contract.md](../data-contract/copilot-tool-contract.md) |
| ADR-013 | Country/Sector/Source Adapter Pattern | [system-architecture.md](../architecture/system-architecture.md) |

---

## ADR-007: Pilot Geography -- Andhra Pradesh (West Godavari + YSR Kadapa)

**Status:** Accepted | **Date:** 2026-09-24

**Decision:** Pilot using West Godavari (AP, LGD 527) and YSR Kadapa.

**Reason:**
1. West Godavari (~84% JJM coverage) provides a real, non-trivial gap for demonstration
2. YSR Kadapa (~100% JJM coverage) provides a natural contrast case for conflict detection
3. AP 2022 district reorganization (13->26 districts) creates a realistic stress test for the LGD historical mapping table
4. Both districts have village-level JJM data available

**Consequence:** The `lgd_historical_mapping` table must be validated against AP 2022 reorganization data before P1.

---

## ADR-008: Synthetic Data Isolation Policy

**Status:** Accepted | **Date:** 2026-09-24

**Decision:** All synthetic data carries `is_synthetic = TRUE` and is segregated in all aggregations, displays, and calculations.

**Reason:** Evidence integrity is a core product promise. If synthetic signals were mixed with real demand, the entire platform's credibility fails. A visible `[SYNTHETIC]` badge on every synthetic item demonstrates commitment to evidence integrity that will resonate with judges.

**Enforcement:** `is_synthetic` is a NOT NULL field with no default -- must be explicitly set on every signal creation.

---

## ADR-009: Deterministic Priority Score

**Status:** Accepted | **Date:** 2026-09-24

**Decision:** The priority score is calculated by a deterministic weighted formula (v1.0.0) implemented in backend code. Gemini never calculates it.

**Formula:** `score = 0.40*gap_pct + 0.30*demand + 0.20*population + 0.10*quality`

**Versioned:** `priority_schema_version = "1.0.0"` stored on every assessment.

**Reason:** Reproducibility, auditability, and trust. Any policymaker or auditor can recalculate the score from the stored factor values without access to AI.

---

## ADR-010: Tabular-Only Spatial Strategy

**Status:** Accepted | **Date:** 2026-09-24

**Decision:** No spatial geometry processing in the MVP. All geographic operations are tabular joins on LGD codes.

**Reason:** PostGIS, WFS queries, and spatial intersection analysis add 2-3 days of infrastructure risk to a 6-day sprint. The intelligence value (gap and priority) is delivered through tabular evidence, not through geographic analysis.

**Map role:** Google Maps is used only for pin visualization (district centroid lat/lng). Pins are contextual presentation, not core intelligence.

---

## ADR-011: Gemini Multimodal Audio over Separate STT

**Status:** Accepted | **Date:** 2026-09-24

**Decision:** Pass citizen audio directly to Gemini 2.0 Flash as multimodal input. No separate Speech-to-Text pipeline.

**Reason:** One API call instead of two; simpler implementation; Gemini handles multilingual audio without pre-configuration.

**Risk:** Audio support for specific Indian languages (especially Telugu) must be verified. Fallback: text submission prompt.

---

## ADR-012: Copilot Security Model

**Status:** Accepted | **Date:** 2026-09-24

**Decision:** All Copilot tools are read-only, hard-coded in an allowlist, and validated by Pydantic schemas. No freeform SQL.

**Reason:** The Copilot interacts with authenticated policymakers, but the tool execution surface must be minimal. An incorrectly prompted Copilot should be unable to write data, execute arbitrary queries, or access unauthorized reports.

---

## ADR-013: Country/Sector/Source Adapter Pattern

**Status:** Accepted | **Date:** 2026-09-24

**Decision:** The architecture explicitly defines three adapter types (Country, Sector, Source) for extensibility, but implements only the India/Water/JJM adapter in the MVP.

**Reason:** The challenge requires demonstrating scalability across India and conceptually to other contexts. Documenting the adapter interface shows architectural thinking without adding implementation risk.

**Consequence:** No code is written for Road, Health, or non-India adapters. The interfaces are documented; implementation is deferred.
