# Architecture Adversarial Review

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Date: 2026-09-24
> Reviewer: Adversarial Senior Architect

This document contains a critical adversarial review of Architecture V1, identifying inconsistencies, risks, and required changes before the architecture freeze.

---

## 1. TOP 10 CRITICAL FINDINGS

1. **[CRITICAL] Audio Extraction Risk (ADR-011):** Relying entirely on `gemini-2.0-flash` multimodal audio for regional Indian languages (Telugu/Hindi) without a dedicated Speech-to-Text (STT) fallback is extremely risky. If the model struggles with accents, the flagship inclusion feature fails completely.
2. **[CRITICAL] AP 2022 Geography Mismatch:** The LGD (post-2022, 26 districts) vs JJM (pre-2022, 13 districts) mapping is assumed to be solvable via a `lgd_historical_mapping` table. If this manual mapping takes longer than 4 hours to build, the entire P1 vertical slice is blocked.
3. **[CRITICAL] Map vs. Tabular Contradiction:** `ux-architecture.md` makes the Map the default landing view, while `ADR-010` and `system-architecture.md` deliberately minimize spatial features. If we have no village polygons and only district centroids, the Map will look sparse and unimpressive as a primary UI.
4. **[CRITICAL] Useless Copilot Tool:** `copilot-tool-contract.md` includes `list_overlapping_interventions`, but notes it will always return "MISSING" in the MVP. We should never demo a tool that intentionally fails to return data.
5. **[CRITICAL] Demand Spam Vulnerability:** The priority formula weighs "Citizen Demand" at 30%. The `idempotency_key` only hashes text and timestamps. A simple bot script could submit 10,000 unique strings, instantly forcing any district to "CRITICAL" priority.
6. **[CRITICAL] BigQuery Over-engineering:** For a 6-day hackathon, configuring BigQuery, Cloud Storage, Secret Manager, Cloud Run, and Firebase IAM roles will consume an entire day. A simpler Cloud SQL (PostgreSQL) setup might be faster for a team familiar with it.
7. **[CRITICAL] Mission Antyodaya Scope Creep:** `implementation-plan.md` lists Mission Antyodaya as a SHOULD, but it isn't used in the priority formula or gap arithmetic. Ingesting it adds risk for zero functional intelligence gain in the MVP.
8. **[HIGH] Lack of Geocoding Fallback:** The Map relies on Google Maps Geocoding API to place district pins. If the API doesn't perfectly recognize the LGD district names, pins will be missing. We need hardcoded fallback coordinates for the pilot districts.
9. **[HIGH] Secret Management Cold Starts:** `deployment-architecture.md` specifies loading secrets from Secret Manager at runtime. If the service account lacks permissions, Cloud Run instances will crash loop on startup.
10. **[HIGH] Synthetic Data Leakage in priority:** If the `include_synthetic` flag default logic fails in the backend, test data will alter the official priority score, violating the core evidence integrity principle.

---

## 2. REQUIRED ARCHITECTURE CHANGES

1. **Change Default UX Landing:** Update `ux-architecture.md` to make the **Hotspot Table** the default landing view, moving the Map to a secondary tab. This aligns with the tabular-first strategy (ADR-010).
2. **Add STT Fallback Plan:** Update `ai-architecture.md` and `implementation-plan.md` to include a standard Google Cloud Speech-to-Text fallback if Gemini multimodal audio extraction fails during Day 1 testing.
3. **Remove Broken Copilot Tools:** Delete `list_overlapping_interventions` from `copilot-tool-contract.md` and `ai-architecture.md`. Only include tools that work with MVP data.
4. **Hardcode Pilot Coordinates:** Update `deployment-architecture.md` to require a static JSON file with lat/lng coordinates for all AP districts to bypass Geocoding API risks.
5. **Drop Mission Antyodaya:** Remove Mission Antyodaya from the MVP critical path and data architecture completely. Focus 100% on JJM to guarantee completion.
6. **Add Rate Limiting / Spam Protection:** Update `security-architecture.md` and the Priority Engine to cap the maximum influence of citizen demand for a single village within a 24-hour window.

---

## 3. WHAT SHOULD BE REMOVED

- **`list_overlapping_interventions` Tool:** Remove entirely.
- **Mission Antyodaya Data Pipeline:** Remove from Phase P1/P2.
- **Map-First UX Flow:** Remove the map as the primary dashboard entry point.

---

## 4. WHAT SHOULD BE DEFERRED

- **Admin Weight Configuration UI:** Hardcode the `v1.0.0` priority weights for the hackathon. Do not build an admin UI to change them dynamically.
- **Census 2011 Data:** Unless strictly required for population weighting, defer this. If JJM provides `total_households`, use that as the proxy for population impact instead of joining a third dataset.

---

## 5. WHAT SHOULD REMAIN EXACTLY AS-IS

- **Water (JJM) Deep Sector:** The arithmetic gap calculation (`total_hh - fhtc_hh`) is the strongest, most defensible part of the architecture.
- **LGD Canonical Spine:** Despite the AP 2022 mapping pain, this is the only mathematically sound way to join data nationally.
- **Strict AI/Deterministic Boundary:** The separation of Gemini (extraction/explanation) from Code (calculation/resolution) is a massive competitive advantage for judges who understand AI hallucinations.
- **Evidence Ledger:** The append-only provenance tracking is the platform's core trust mechanism.
- **Synthetic Data Isolation:** The `[SYNTHETIC]` badge approach is excellent for safe demoing.

---

## 6. QUESTIONS THAT REQUIRE GOOGLE-SPECIFIC VALIDATION

1. Does `gemini-2.0-flash` via the Google AI Studio API support passing `Part.from_uri()` (GCS audio) AND `response_schema` (structured output) in the exact same API call?
2. Is Telugu audio transcription accurate enough natively in Gemini 2.0 Flash, or is a specialized regional STT model strictly necessary?
3. Does the Cloud Run free tier in `asia-south1` support scaling to zero without egregious cold start penalties (>5s)?

---

## 7. QUESTIONS THAT REQUIRE REAL-DATA VALIDATION

1. **AP 2022 Reorganization:** Can we successfully map the pre-2022 JJM 13 districts to the post-2022 LGD 26 districts within 4 hours using fuzzy matching?
2. **JJM Data Completeness:** Does the downloaded JJM CSV actually contain `total_households` and `fhtc_households` for *every* village in West Godavari, or are there massive gaps?
3. **LGD Village Names:** Are the village names in LGD spelled similarly enough to the village names in JJM to allow Levenshtein distance matching?

---

## 8. FINAL "READY FOR GOOGLE VALIDATION?" VERDICT

**NO**

**Reason:** The architecture contains internal contradictions regarding the Map UX vs. Tabular data reality, includes a demo-breaking "Missing Data" Copilot tool, and carries extreme risk regarding direct audio extraction without an explicit STT fallback.

Once the "Required Architecture Changes" (Section 2) are applied, the architecture will be **YES** (Ready for Freeze and Validation).
