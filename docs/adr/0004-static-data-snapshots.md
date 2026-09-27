# ADR-004: Static Data Snapshots Over Live Government APIs

**Status:** Accepted
**Date:** 2026-09-24

---

## Context

The platform requires government data (LGD, JJM, Mission Antyodaya) as the foundation for all gap calculations. Two approaches exist:

1. Query live government APIs at runtime
2. Download static snapshots and load into BigQuery

The research phase found that live government portal reliability is a critical risk.

## Failure Modes Identified

| Source | Live API Risk |
|--------|--------------|
| LGD NAPIX API | Requires NICSI auth registration; non-trivial approval process; auth token management |
| JJM Dashboard | No public API; HTML scraping only; page structure changes frequently |
| Mission Antyodaya Portal | No documented API; data available only as download |
| e-GramSwaraj | No public API for GPDP data |
| APSAC WMS | Image tiles only (WMS); no WFS available for data queries |

## Decision

All data sources are loaded as **pre-processed static snapshots** into BigQuery before the hackathon demo.

- LGD: Bulk CSV downloaded from lgd.gov.in (no API auth required)
- JJM: District and village-level CSV/PDF extracts downloaded from jjm.gov.in
- Mission Antyodaya: Annual survey data available as downloadable CSV
- Census 2011: Village Directory available as static files

Each snapshot is labeled with `data_as_of` (source date) and `ingested_at` (when we loaded it).

No live government API dependencies in any demo critical path.

## Consequences

### Positive
- Demo stability guaranteed (no runtime API failures)
- No auth management for NAPIX or other portals
- All data loaded and verified before P1 vertical slice
- Data quality issues discovered at ingestion time, not demo time

### Negative
- Data may be several months old by submission date
- Requires manual re-ingestion for updates (acceptable for hackathon)

### Transparency
The platform explicitly labels all data with `data_as_of` dates in every report and dashboard view. "Data as of 2025-01-01" is a feature, not a bug -- it demonstrates provenance commitment.

---

# ADR-005: AI vs Deterministic Boundary

**Status:** Accepted
**Date:** 2026-09-24

---

## Context

The platform uses Gemini for natural language understanding. However, the core value proposition -- evidence-backed, transparent priority -- depends on calculations being reproducible and auditable.

If Gemini calculates the gap or priority score, the system cannot explain how the number was derived, cannot version the formula, and risks hallucinating statistics.

## Decision

**Strict boundary:**

| Task | Assigned To | Why |
|------|------------|-----|
| Multilingual understanding | Gemini | Only AI can do this |
| Civic need classification | Gemini | Semantic judgment |
| Location expression extraction | Gemini | Natural language |
| Urgency signal detection | Gemini | Tone/sentiment |
| Copilot explanation | Gemini | Natural language generation |
| LGD code resolution | Deterministic code | Must be exact and auditable |
| Gap arithmetic | Deterministic code | total_hh - fhtc_hh -- never LLM |
| Priority calculation | Deterministic code | Weighted formula; versioned; auditable |
| Conflict detection | Deterministic code | Comparing specific field values |
| Provenance recording | Deterministic code | Cannot be delegated |
| Evidence database writes | Deterministic code | Data integrity |

## Enforcement Mechanisms

1. Gemini receives `response_schema` forcing it to output JSON only -- no statistics
2. Pydantic validates all Gemini outputs before any field is used
3. Gap and priority calculations happen AFTER Gemini call returns, in pure Python
4. Copilot receives pre-calculated values from tool results -- generates explanation only
5. System prompt explicitly prohibits Gemini from producing infrastructure statistics

## Consequences

### Positive
- Gap and priority calculations are fully reproducible and versioned
- Gemini hallucination cannot reach the authoritative output layer
- Formula changes create new schema versions (transparent to policymakers)
- Engineers can unit test all calculations without mocking Gemini

### Negative
- Two-step process (Gemini extract -> backend calculate) adds latency
- Acceptable: demo latency is not the primary judging criterion

---

# ADR-006: Cloud Run Monorepo Deployment

**Status:** Accepted
**Date:** 2026-09-24

---

## Context

The platform needs a deployable architecture that:
- Can be deployed end-to-end within Day 1-2 of the sprint
- Produces a live URL for submission
- Supports both Python backend and Next.js frontend
- Does not require cluster management

## Decision

Two Cloud Run services from a single monorepo:
- `civic-backend`: Python FastAPI (port 8080)
- `civic-frontend`: Next.js (port 3000)

No Kubernetes. No message queues. No microservices.

## Consequences

### Positive
- Simple deploy: one Dockerfile per service
- Scales to zero (cost management)
- Single source of truth
- CI/CD can deploy both with GitHub Actions

### Negative
- Frontend/backend coupling in one repo (acceptable at MVP scale)
- If one service fails, both may need redeployment

### Alternative Considered
- Cloud Functions: Rejected because FastAPI structure is more appropriate for multi-endpoint REST API
- GKE: Rejected because Kubernetes management overhead is unacceptable for a 6-day sprint
