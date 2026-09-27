# Project Context: Civic Demand Intelligence & Planning Platform

> Living document. Update when stack, constraints, or phase changes.
> Architecture V1 -- 2026-09-24

---

## Identity

| Field | Value |
|-------|-------|
| Project | Civic Demand Intelligence & Planning Platform |
| Hackathon | Build with AI: Code for Communities -- Second Edition |
| Track | Track 1: AI for Digital Public Infrastructure & Governance |
| Theme | BRICS -- Innovation |
| Deadline | ~6 days from architecture freeze |
| Phase | Architecture V1 (pre-implementation) |

---

## Chosen Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| AI/LLM | Gemini 2.0 Flash (Google AI Studio API) | Structured output + multimodal audio + multilingual; mandatory Google AI |
| Backend | Python 3.11 + FastAPI | Fast to build; strong Pydantic integration for schema validation |
| API hosting | Cloud Run | Serverless, scales to zero, single Dockerfile, fast deploy |
| Data warehouse | BigQuery | SQL analytics at scale; no operational overhead; free tier viable for MVP |
| Object storage | Cloud Storage | Raw source snapshots; audio files; pre-processed static data |
| Auth | Firebase Authentication | Managed auth; Google provider; integrates with Next.js easily |
| Maps | Google Maps Platform JS API + Geocoding API | District-level pins; not deep GIS |
| Secrets | Google Secret Manager | API keys, BigQuery credentials, Gemini key |
| Frontend | Next.js 14 (App Router) | SSR + API routes; strong React ecosystem |
| Hosting (FE) | Firebase Hosting or Cloud Run (TBD) | Static or containerized depending on build |
| Validation | Pydantic v2 | Schema validation for all Gemini structured outputs |

---

## Architecture Decisions (Locked)

### ADR-001: LGD as Canonical Geographic Identity
- All geographies resolved to LGD numeric codes
- Source-native IDs preserved alongside canonical codes
- Tabular joins ONLY -- no PostGIS, no WMS, no GIS spatial queries in MVP critical path

### ADR-002: Water / JJM as MVP Deep Sector
- Gap = `total_households - functional_tap_connections`
- Pure arithmetic -- no LLM involvement in gap calculation
- Other sectors (roads, sanitation, health) deferred to post-MVP adapters

### ADR-003: BigQuery as Analytical Backbone
- All canonical data and derived intelligence stored in BigQuery
- Relational structure using LGD codes as foreign keys
- No graph database, no document store in MVP

### ADR-004: Static Data Snapshots (No Live Government APIs)
- LGD, JJM, Mission Antyodaya loaded as pre-processed BigQuery tables
- NAPIX API, APSAC WMS, e-GramSwaraj scraping all excluded from MVP critical path
- Snapshots labeled with data_as_of and ingested_at timestamps

### ADR-005: Gemini Interprets; Deterministic Code Calculates
- Gemini: multilingual extraction, civic need classification, Copilot explanation
- Backend: entity resolution, gap calculation, priority scoring, provenance, conflict detection
- Gemini NEVER writes to database, executes SQL, or produces authoritative statistics

### ADR-006: Monorepo, Two Cloud Run Services
- One backend (FastAPI + Python)
- One frontend (Next.js -- either Cloud Run or Firebase Hosting)
- No microservices; no message queues in MVP

### ADR-007: Pilot Geography = Andhra Pradesh (West Godavari + YSR Kadapa)
- Post-2022 AP reorganization stress test built in
- Contrast case (100% vs 84% coverage) enables conflict detection demo

### ADR-008: Synthetic Data Isolated and Labeled
- All synthetic citizen signals carry `is_synthetic: true` flag
- UI renders [SYNTHETIC SIGNAL] badge -- never presented as real data
- Synthetic data cannot contaminate the evidence ledger

### ADR-009: Priority Score is Deterministic and Versioned
- Formula defined in code; Gemini NEVER calculates it
- `priority_schema_version` field tracks formula changes
- Factor contributions exposed in report

### ADR-010: Maps are Contextual, Not Core
- Google Maps used for district pin visualization
- LGD boundary polygons optional (preprocessed GeoJSON if used)
- No real-time spatial analysis in MVP

---

## Locked Product Principles

1. Central object is the **CIVIC NEED**
2. Citizen requests: text / voice / messaging / multilingual
3. Different expressions of the same problem normalized to one civic need
4. Multiple linked needs representable
5. India-first; adapter pattern for future countries
6. LGD is canonical administrative identity
7. Source-native IDs preserved
8. Source-to-canonical reconciliation explicit and traceable
9. Missing data is a legitimate state (AVAILABLE / PARTIAL / MISSING / CONFLICTING / LOW_CONFIDENCE)
10. Missing government data NEVER invented by LLM
11. Conflicting official evidence preserved and exposed
12. Synthetic citizen data explicitly labelled
13. Sensitive identity attributes not used as priority weights
14. AI interprets, structures, connects, explains
15. Deterministic code validates, resolves, aggregates, calculates, ranks
16. Policymakers remain responsible for final action

---

## Constraints

| Constraint | Description |
|-----------|-------------|
| Time | ~6 days to prototype submission |
| AI | Google AI is mandatory |
| Data | Real or realistic public data required |
| Deployment | Live deployed link required for submission |
| Demo | Working end-to-end video (3-5 min) required |
| Scale | Must demonstrate cross-India scalability conceptually |
| GIS | No complex GIS spatial joins in MVP critical path |
| Live APIs | No live government portal dependencies for core demo |

---

## Current Implementation Phase

**Phase: Architecture V1 Complete -- Pre-Implementation**

Next phase: P0 Foundation
- BigQuery schema creation
- Data ingestion scripts (LGD, JJM, Mission Antyodaya CSVs)
- FastAPI skeleton with Gemini integration
- Cloud Run Dockerfile
- Firebase Auth setup

---

## Do-Not-Break Boundaries

| Boundary | Rule |
|----------|------|
| LLM Hallucination | Gemini NEVER produces official statistics or gap numbers |
| Synthetic data | ALWAYS labeled; NEVER mixed into evidence ledger without flag |
| Priority score | ALWAYS calculated by deterministic code, NEVER by Gemini |
| Source provenance | EVERY evidence item must carry source, data_as_of, ingested_at |
| LGD resolution | NEVER silently drop unresolved geographies; always expose resolution status |
| Conflict handling | NEVER silently average conflicting sources; ALWAYS preserve both |
| Missing data | NEVER convert MISSING to zero; ALWAYS expose data quality state |
| Copilot tools | ALL read-only; ALL backend-validated; NO arbitrary SQL |
| Citizen input | ALWAYS treated as untrusted; sanitized before Gemini prompt construction |

---

## Validation Commands (To be added post-implementation)

```bash
# Backend
pytest backend/tests/

# Frontend
npm run lint && npm run build

# Integration
# See docs/architecture/deployment-architecture.md
```

---

## References

- [CHALLENGE_CONTEXT.md](CHALLENGE_CONTEXT.md)
- [GEMINI_PRE_ARCHITECTURE_RESEARCH.md](GEMINI_PRE_ARCHITECTURE_RESEARCH.md)
- [docs/architecture/](docs/architecture/)
- [docs/data-contract/](docs/data-contract/)
- [docs/adr/](docs/adr/)
