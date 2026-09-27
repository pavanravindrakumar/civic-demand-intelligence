# Architecture Master Digest
> Civic Demand Intelligence & Planning Platform -- Architecture V1.1
> Date: 2026-09-24

This is a synthesized, decision-oriented digest of the complete architecture package for external review.

---

## 1. PROJECT IDENTITY

- **Exact Product Definition:** An AI-powered intelligence layer that transforms fragmented citizen development requests into evidence-backed, transparent priorities for policymakers.
- **Core Thesis:** AI should interpret human needs and explain complex data, but deterministic code must calculate public infrastructure gaps and priority rankings to ensure auditability and prevent hallucination.
- **What the Product is NOT:** It is not a complaint portal, a generic chatbot, or a live government data scraper.
- **Target Users:**
  - *Citizens (Input):* Provide unstructured, multilingual signals (voice/text).
  - *Policymakers (Output):* Consume dense, evidence-grounded Intelligence Reports and use the Copilot for Q&A.
- **Core User Journey:** Citizen submits voice signal -> AI extracts civic need -> System matches to versioned Geography -> System calculates gap against JJM data -> Policymaker views Map+Hotspot List and asks Copilot for context.

---

## 2. CHALLENGE ALIGNMENT

| Challenge Requirement | Architecture Capability | Implementation Mechanism |
|-----------------------|-------------------------|--------------------------|
| Problem-Solution Fit (20%) | Actionable intelligence layer | Transforms raw complaints into structured `IntelligenceReports` |
| AI / Technical Execution (25%) | Multimodal extraction + Grounded Copilot | Configurable `GEMINI_MODEL` (audio/text) + STT fallback + Function Calling |
| Depth & Reach India (20%) | National scalability | Versioned geography model with LGD mapping |
| Deployability (20%) | Zero-ops serverless deployment | Cloud Run (FastAPI/Next.js) + BigQuery + Firebase Auth |
| Impact Potential (15%) | Scalable deep sector focus | Water access (JJM) affects 140M+ rural households |

---

## 3. SYSTEM ARCHITECTURE

**Complete Architecture in One Diagram:**
*(Refer to `docs/architecture/system-architecture.md` for full Mermaid diagrams)*
Citizen -> Cloud Run (Next.js) -> Cloud Run (FastAPI) -> Gemini/STT (Extraction) -> BigQuery (Versioned Geo & Gap Calc) -> BigQuery (Storage/Materialized Views) -> Cloud Run (FastAPI) -> Dashboard (Map + Table) / Copilot.

- **Components & Boundaries:**
  - `civic-frontend`: Next.js (Port 3000) - Citizen portal & Policymaker Map+Hotspot UX.
  - `civic-backend`: FastAPI (Port 8080) - API routes, data orchestration, Gemini/STT integration.
  - `BigQuery`: Canonical store, materialized intelligence views, evidence ledger.
  - `Cloud Storage`: Raw data snapshots & ephemeral citizen audio (24h TTL).
- **Data Flow:** Citizen text/audio -> Backend -> Gemini/STT -> Structured JSON -> Backend -> BQ -> Materialized View -> Frontend.

---

## 4. AI / DETERMINISTIC BOUNDARY

**STRICT SEPARATION OF CONCERNS:**

| Actor | Responsibilities |
|-------|------------------|
| **Configurable Gemini Model (AI)** | Multilingual understanding, civic need classification, urgency detection, grounding/explaining calculated reports via Copilot tools. **(NEVER calculates gaps).** |
| **Backend Code (Deterministic)** | Geography version resolution, gap arithmetic (`total_hh` - `fhtc_hh`), versioned priority formula, duplicate detection, rate limiting. |
| **Policymaker (Human)** | Reviews evidence conflicts, makes final policy decisions based on transparent intelligence reports. |

---

## 5. DATA ARCHITECTURE

- **Canonical Entities:** `CanonicalGeography`, `CivicNeed`, `CitizenSignal`, `EvidenceItem`, `GapAssessment`, `PriorityAssessment`, `IntelligenceReport`.
- **Layers:** Raw (GCS) -> Normalized (BQ) -> Canonical (BQ) -> Derived (BQ) -> Materialized (BQ precomputed for dashboard).
- **Geography Model:** Internal stable `geography_id` + versioned LGD identifier + source-native IDs. Handles evolving administrative boundaries.
- **Evidence Model:** Immutable records with `data_as_of`.
- **Conflict Model:** Exposes discrepancies (e.g., Citizen vs JJM) directly.
- **Missing Data:** Modeled explicitly (`AVAILABLE`, `PARTIAL`, `MISSING`, `CONFLICTING`).
- **Synthetic Data:** Mandatory `is_synthetic = true` boolean on all signals, excluded from official metrics.
- **Demand Anti-Manipulation:** Explicit duplicate detection, rate limiting, and bounded influence (saturation) for citizen signals.

---

## 6. DATA SOURCES

| Source | Role | Geo Level | Identifier | Join Method | Freshness | MVP Status |
|--------|------|-----------|------------|-------------|-----------|------------|
| **LGD** | CORE | Village | Versioned LGD | Direct | Snapshot | **MUST** |
| **JJM** | CORE | Village | Native Name | Fuzzy+Mapping | Snapshot | **MUST** |
| **Mission Antyodaya** | SUPPORTING | GP | Native GP | Fuzzy String | 2022-23 | OPTIONAL |
| **Census 2011** | CONTEXTUAL | Village | Census Code | Mapping | 2011 | OPTIONAL |
| **PMGSY / Roads** | FUTURE | Block/GP | - | Spatial | N/A | DEFER |
| **LGD NAPIX API** | REFRESH | - | - | - | Live API | FUTURE |

---

## 7. DEEP-SECTOR DECISION

- **Selected Sector:** Water and Sanitation (Jal Jeevan Mission - JJM).
- **Measurable Chain:** Signal -> Versioned Geo -> Query JJM Village Data -> Subtract FHTC from Total -> "Reported Household Tap-Connection Gap".
- **Why:** The gap is deterministic arithmetic. It requires zero spatial routing or LLM estimation, ensuring mathematical auditability.
- **Deferred Alternative:** Roads (PMGSY) requires complex spatial network analysis, deferred to optional future enhancements.

---

## 8. PRIORITY ENGINE

- **Configurable Versioned Policy:** Priority is not an arbitrary magic number. It uses normalized inputs, bounded saturation (to prevent spam manipulation), and explicit factor contributions.
- **Factors:** Gap Severity, Population Impact, Validated Citizen Demand (Bounded), Urgency / Essentiality, Evidence Quality.
- **Missing/Confidence Behavior:** If evidence is missing, the quality multiplier heavily penalizes the score.

---

## 9. EVIDENCE LEDGER

- **What:** An append-only audit trail (`evidence_ledger`).
- **Stores:** Source, source-native ID, canonical geography, source version, `data_as_of`, processing version, calculation version, policy version, assumptions, data quality, synthetic fraction, conflict info.
- **Traceability:** Every report links back through ledger steps.

---

## 10. COPILOT

**All tools are READ-ONLY BigQuery queries.**

| Tool Name | Purpose | Auth & Security |
|-----------|---------|-----------------|
| `get_hotspot_details` | District demand/gap summary | Pydantic validated args, Token required |
| `get_intelligence_report` | Fetch full report by ID | Report ID validation |
| `explain_priority_score` | Break down math of a score | Priority ID validation |
| `show_evidence_conflict` | Compare conflicting sources | Conflict ID validation |
| `compare_policy_weights` | "What if" weighting exploration | Max 3 scenarios limit |
| `get_jjm_scheme_status` | Actual JJM scheme evidence | Real data lookup |

*(Note: `list_overlapping_interventions` removed from MVP)*

---

## 11. UX

- **Citizen:** Mobile-first, single form, multilingual voice/text toggle.
- **Policymaker:** Map + Hotspot List Split UX.
  - *Geographic Context:* Data-driven Map (precomputed geometry/centroids, NO hardcoded coordinates).
  - *Operational Selection:* Hotspot Table.
  - *Report Detail:* Dense, evidence-linked report.
- **Trust Model:** UI clearly distinguishes AI Interpretation from Deterministic Evidence, and exposes Missing, Partial, Conflicting, Synthetic, and Historical states.

---

## 12. SECURITY

- **Threat Model:** Malicious citizens (injection/spam), PII exposure, synthetic leakage.
- **Anti-Manipulation:** `idempotency_key`, rate limits, duplicate detection, bounded demand influence.
- **Audio Retention:** GCS bucket lifecycle rule deletes audio after 24 hours.
- **Prompt Injection:** Input sanitization + strict Pydantic enforcement.
- **Auth:** Firebase Google OAuth for Dashboard.

---

## 13. DEPLOYMENT

- **Topology:** GCP `asia-south1`.
- **Services:** `civic-backend` (FastAPI), `civic-frontend` (Next.js). No extra microservices.
- **Data:** BigQuery (with materialized views for performance), Cloud Storage.
- **Secrets:** Secret Manager.

---

## 14. SIX-DAY MVP

- **P0 (Foundation - MUST):** GCP Setup, BigQuery Tables, LGD/JJM CSV ingestion, Cloud Run skeleton.
- **P1 (Vertical Slice - MUST):** Citizen Signal -> Geo -> JJM -> Tap-Connection Gap -> Priority -> Report -> Map+Hotspot List -> Copilot Explanation.
- **P2 (Intelligence - MUST):** Versioned Geo matching, Priority Policy Engine, Conflict detector.
- **P3 (UX - MUST/SHOULD):** Map+List, Copilot, Voice (Gemini primary + STT fallback).
- **P4 (Hardening - MUST):** Security, Rate limiting, Materialized BQ Views.
- **P5 (Submission - MUST):** Video, Pitch.

---

## 15. ARCHITECTURAL DECISIONS (ADRs)

| ADR | Decision | Reason |
|-----|----------|--------|
| **001 (Rev)** | Versioned Geo Model | Administrative boundaries evolve (AP 13->26->28). |
| **002 (Rev)** | "Reported Household Tap-Connection Gap" | Precision. Avoids "absolute" claims. |
| **005** | Strict AI Boundary | Prevent LLM math hallucination. |
| **008** | Synthetic Data Isolation | Explicit `is_synthetic = true` to protect integrity. |
| **010** | Tabular MVP + Optional Spatial | BQ MVP primary path, spatial is optional enhancement. |
| **011 (Rev)** | Gemini Audio + GCP STT Fallback | Mitigates risk of regional dialect failures. |
| **014 (New)** | Demand Anti-Manipulation | Prevents bot spam from overriding priority engine. |

---

## 16. CURRENT ASSUMPTIONS (Pending Verification)

1. Selected `GEMINI_MODEL` supports multimodal audio and structured output concurrently.
2. GCP STT fallback supports Telugu adequately if Gemini fails.
3. BigQuery materialized views will keep dashboard load times under 1 second.
4. Quotas for the configured Gemini model allow sufficient throughput for judging.

---

## 17. KNOWN RISKS

| Risk | Impact | Likelihood | Mitigation | Fallback |
|------|--------|------------|------------|----------|
| Geography Version Mismatch | HIGH | HIGH | Versioned reconciliation mapping | Flag as UNRESOLVED |
| Gemini Audio Failure | MED | MED | GCP STT Fallback | Text-only submission |
| Demand Manipulation | HIGH | LOW | Bounded saturation & idempotency | Admin override |

---

## 18. ARCHITECTURAL CONFLICTS RESOLVED (V1.1)

- Map vs. Tabular conflict resolved via Map + Hotspot List split experience.
- Missing Copilot tool (`interventions`) removed; replaced with actual JJM status tool.
- Static LGD assumption replaced with Versioned Geography model.
- Unbounded demand priority manipulation secured via saturation bounds.

---

## 19. QUESTIONABLE DECISIONS (To Challenge)

1. **BigQuery for MVP:** Still heavy for a 6-day sprint, but retained for analytical scaling and materialized views.
2. **Tabular First:** Prioritizing tabular joins over PostGIS spatial routing limits "flashy" GIS demos, but ensures the product actually works in 6 days.

---

## 20. ARCHITECTURE REVIEW CHECKPOINT

| Item | Action | Reasoning |
|------|--------|-----------|
| **LGD Versioning** | **VERIFIED** | Solves evolving boundary problem. |
| **Reported Tap Gap** | **VERIFIED** | Precise, deterministic, mathematically sound. |
| **Gemini + STT Fallback**| **VERIFIED** | robust multimodal support. |
| **Demand Saturation** | **VERIFIED** | Prevents priority manipulation. |
| **BQ Materialized Views**| **VERIFIED** | Fixes dashboard latency concerns. |
