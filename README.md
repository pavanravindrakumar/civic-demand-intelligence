# Civic Demand Intelligence & Planning Platform

> **Track 1 — AI for Digital Public Infrastructure & Governance**
> Build with AI: Code for Communities — Second Edition | BRICS Theme: Innovation

---

## What Is This?

The **Civic Demand Intelligence & Planning Platform** is an AI-powered intelligence layer that transforms fragmented citizen development requests into evidence-backed, transparent priorities for policymakers.

It is **not** a complaint portal. It is not a chatbot. It is not a generic dashboard.

It is a platform that:

1. Captures citizen development signals (text / voice / multilingual)
2. Uses Gemini to extract the underlying **Civic Need** from fragmented expressions
3. Resolves the need to a canonical **LGD administrative geography**
4. Queries structured public evidence (JJM, Mission Antyodaya, Census) **deterministically**
5. Calculates an **evidence-backed infrastructure gap** without LLM invention
6. Produces a **Civic Intelligence Report** with transparent priority, provenance, and confidence
7. Presents an **AI Copilot** to help policymakers navigate, question, and understand findings

---

## Core Transformation

```
Citizen Signal (voice / text / multilingual)
  -> Gemini Civic Need Extraction (structured JSON)
  -> LGD Geography Resolution (deterministic lookup)
  -> Public Evidence Query (JJM / Mission Antyodaya)
  -> Deterministic Gap Calculation (SQL arithmetic)
  -> Priority Score (transparent, versioned formula)
  -> Civic Intelligence Report (provenance + confidence)
  -> Policymaker Decision Support (AI Copilot)
```

---

## Six-Day MVP Scope

| Phase | Focus | Days |
|-------|-------|------|
| P0 Foundation | Data ingestion, schema, deployment skeleton | Day 1-2 |
| P1 Vertical Slice | End-to-end signal to report (Water/JJM) | Day 2-3 |
| P2 Intelligence | Priority scoring, conflict detection, hotspot map | Day 3-4 |
| P3 UX | Policymaker dashboard, Copilot, polish | Day 4-5 |
| P4 Hardening | Security, provenance, error states, demo prep | Day 5-6 |
| P5 Submission | Video, deck, deployed link | Day 6 |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| AI / LLM | Gemini 2.0 Flash (via Google AI Studio API) |
| Backend | Python / FastAPI on Cloud Run |
| Database | BigQuery (canonical data warehouse) |
| Storage | Cloud Storage (raw source snapshots) |
| Auth | Firebase Authentication |
| Maps | Google Maps Platform (Geocoding + JS Maps) |
| Secrets | Secret Manager |
| Frontend | Next.js (React) |

---

## Deep Sector (MVP)

**Water and Sanitation -- Jal Jeevan Mission (JJM)**

Gap logic: `unmet_demand = total_households - functional_tap_connections`

No spatial analysis. No LLM arithmetic. Pure SQL subtraction against verified government data.

---

## Pilot Geography (MVP)

| District | State | JJM Coverage | Demo Purpose |
|----------|-------|-------------|--------------|
| West Godavari | Andhra Pradesh | ~84% | Complex water-quality crisis; post-2022 AP reorganization stress test |
| YSR Kadapa | Andhra Pradesh | ~100% | Conflict detection baseline (flags false citizen claims) |

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md) | Full system architecture with diagrams |
| [docs/architecture/data-architecture.md](docs/architecture/data-architecture.md) | Canonical data model and lifecycle |
| [docs/architecture/ai-architecture.md](docs/architecture/ai-architecture.md) | Gemini usage, boundaries, function calling |
| [docs/architecture/ux-architecture.md](docs/architecture/ux-architecture.md) | Policymaker UX, screens, design system |
| [docs/architecture/security-architecture.md](docs/architecture/security-architecture.md) | Security model, threat model, safeguards |
| [docs/architecture/deployment-architecture.md](docs/architecture/deployment-architecture.md) | Cloud deployment blueprint |
| [docs/architecture/implementation-plan.md](docs/architecture/implementation-plan.md) | Six-day implementation timeline |
| [docs/architecture/risk-register.md](docs/architecture/risk-register.md) | Risks, mitigations, fallbacks |
| [docs/architecture/decision-summary.md](docs/architecture/decision-summary.md) | All architectural decisions at a glance |
| [docs/architecture/google-validation-checklist.md](docs/architecture/google-validation-checklist.md) | Google service assumptions to verify |
| [docs/data-contract/canonical-data-contract.md](docs/data-contract/canonical-data-contract.md) | Master canonical data model |
| [docs/data-contract/citizen-signal-contract.md](docs/data-contract/citizen-signal-contract.md) | Citizen signal ingestion contract |
| [docs/data-contract/evidence-contract.md](docs/data-contract/evidence-contract.md) | Evidence item and provenance contract |
| [docs/data-contract/gap-priority-contract.md](docs/data-contract/gap-priority-contract.md) | Gap assessment and priority contract |
| [docs/data-contract/copilot-tool-contract.md](docs/data-contract/copilot-tool-contract.md) | Copilot tool function-calling contract |
| [docs/adr/](docs/adr/) | Architecture Decision Records |
| [project-context.md](project-context.md) | Stack, constraints, do-not-break rules |

---

## Challenge Alignment

| Criterion | Weight | How We Address It |
|-----------|--------|-------------------|
| Problem-Solution Fit | 20% | Intelligence layer, not a portal -- transforms fragmented demand into planning intelligence |
| AI/Technical Execution | 25% | Gemini multilingual extraction + structured output; deterministic SQL for evidence |
| Depth and Reach Across India | 20% | LGD as national identity spine; sector/country adapter pattern |
| Deployability and Scalability | 20% | Cloud Run + BigQuery; stateless backend; single-command deploy |
| Impact Potential | 15% | Water access gap affects 140M+ rural Indian households; JJM data is national |

---

*Architecture V1 - produced 2026-09-24*
