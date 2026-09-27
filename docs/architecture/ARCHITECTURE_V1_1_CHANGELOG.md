# Architecture V1.1 Changelog

> Civic Demand Intelligence & Planning Platform
> Date: 2026-09-24

This document tracks the mandatory architectural corrections applied during the V1.1 reconciliation pass before Google validation.

| Old Decision | New Decision | Reason | Impact |
|--------------|--------------|--------|--------|
| **Immutable LGD Codes** | **Versioned Geography Model** | Administrative boundaries evolve (e.g., AP 13->26->28 districts). A single static LGD mapping is brittle. | `CanonicalGeography` now uses an internal stable ID mapped to a versioned LGD snapshot. Source data is reconciled against specific geography versions. |
| **"Absolute Unmet Demand"** | **"Reported Household Tap-Connection Gap"** | "Absolute unmet" implies perfect ground truth. "Reported" acknowledges data limitations. | Terminology updated in UI, contracts, and calculations to ensure precision and prevent misleading claims. |
| **Mission Antyodaya Core** | **Mission Antyodaya Optional/Supporting** | Mission Antyodaya ingestion adds risk and shouldn't block the P1 vertical slice. | Moved to P2/Optional. The platform must function completely without it. |
| **Map as Primary UX** | **Map + Hotspot List Split UX** | The map is geographic context; the table is operational reality. If geocoding fails, the table must suffice. | UX updated. Map is an enrichment, not a single point of failure. |
| **Hardcoded Coordinates** | **Data-driven Coordinates** | Hardcoded UI logic for pilot districts is inflexible and scales poorly. | Coordinates (representative points/centroids) are preprocessed and stored in BQ geography tables, passed to the UI. |
| **No GIS** | **Tabular MVP + Optional Spatial Analysis** | Banning GIS prevents future value. It should be allowed as a preprocessed enhancement. | Architecture updated to define tabular joins as the MVP primary path, with spatial routing deferred. |
| **Gemini-only Audio** | **Gemini Primary + GCP STT Fallback** | Gemini 2.0/3.8 may struggle with rural regional dialects without STT. | Added Google Cloud Speech-to-Text as a formal fallback path to ensure audio robustness. |
| **Hardcoded `gemini-2.0-flash`**| **Configurable `GEMINI_MODEL`** | AI models evolve rapidly (e.g. `gemini-3.8-flash`). | Replaced all hardcoded model names with an environment variable. |
| **Arbitrary Priority Formula** | **Configurable, Bounded Priority Engine** | Hardcoded 0.4/0.3 weights and unbounded demand counts invite spam and manipulation. | New formula uses Gap Severity, Population Impact, Validated Citizen Demand (bounded/saturated), Urgency, and Evidence Quality. |
| **Naive Demand Count** | **Demand Anti-Manipulation** | Many duplicate signals do not equal many independent citizens. | Added explicit idempotency, duplicate detection, and bounded saturation to citizen signals. |
| **`list_overlapping_interventions`** | **Removed / Replaced with JJM Status** | Copilot tool returned "MISSING" intentionally in MVP, creating a poor demo experience. | Tool removed. Added a simpler JJM scheme status lookup tool that uses actual snapshot data. |
| **Dynamic BQ Queries** | **Materialized BQ Views** | Running heavy aggregations on every dashboard load causes unpredictable latency. | Added requirement for precomputed/materialized tables for hotspot and report serving. |
