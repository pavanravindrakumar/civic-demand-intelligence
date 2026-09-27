# Architecture V1.1 Review Summary

> Civic Demand Intelligence & Planning Platform
> Date: 2026-09-24

Final review checkpoint before Google validation.

| Feature / Component | Action | Reasoning |
|---------------------|--------|-----------|
| **LGD Geography Backbone** | **MODIFY** | Kept, but modified to a versioned model with an internal stable ID. LGD codes change over time. |
| **Water / JJM Sector** | **KEEP** | Perfect for the MVP due to deterministic arithmetic gap logic. |
| **Mission Antyodaya** | **DEFER** | Kept as an optional enrichment, but removed from the P1 vertical slice critical path. |
| **Priority Engine** | **MODIFY** | Replaced arbitrary hardcoded weights with a configurable policy engine featuring saturated demand bounds to prevent manipulation. |
| **Copilot Intervention Tool**| **REMOVE** | Removed the `list_overlapping_interventions` tool as it lacked MVP data. Replaced with a JJM Scheme Status tool. |
| **Direct Gemini Audio** | **MODIFY** | Kept as primary, but added a mandatory Google Cloud STT fallback path for robust regional language support. |
| **Cloud Run Architecture** | **KEEP** | Two services (FastAPI/Next.js) remains the optimal deployment balance for speed and scale-to-zero cost. |
| **BigQuery Analytics** | **MODIFY** | Kept as the backbone, but mandated materialized/precomputed views for dashboard endpoints to guarantee low latency. |
| **Map UX Strategy** | **MODIFY** | Shifted from Map-primary to a Map + Hotspot List split experience. Coordinates must be data-driven, not hardcoded. |
| **Synthetic Data Isolation**| **KEEP** | The `is_synthetic` flag and UI badging remains the strongest defense for evidence integrity. |
| **Google Quotas & Limits** | **VERIFY** | Must explicitly verify the chosen `GEMINI_MODEL`, audio limits, and BQ query costs before coding. |
