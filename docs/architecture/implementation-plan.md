# Implementation Plan

> Civic Demand Intelligence & Planning Platform -- Architecture FINAL FREEZE
> Six-day sprint from architecture freeze

---

## Strategy: Vertical Slice First

The most important engineering principle for this sprint:

**ONE COMPLETE END-TO-END CHAIN MUST WORK BEFORE ANYTHING ELSE IS ADDED.**

The chain:
```
Citizen Signal (synthetic text)
  -> Gemini Extraction (structured JSON)
  -> LGD Resolution (BQ lookup)
  -> JJM Evidence Query (BQ arithmetic)
  -> Gap Calculation (deterministic)
  -> Priority Score (deterministic formula)
  -> Intelligence Report (stored in BQ)
  -> Dashboard display (basic)
```

Only when this chain works without errors should new features be added.

---

## Phase Breakdown

### P0 -- Foundation (Day 1, target: EOD Day 1)

**Goal:** Data loaded. Services deployed. End-to-end connectivity verified.

**P0 Tasks:**

| Task | Owner | Priority | Risk |
|------|-------|----------|------|
| Create GCP project + enable all APIs | Infra | MUST | Low |
| Create BigQuery dataset + all tables | Backend | MUST | Low |
| Create Cloud Storage buckets | Infra | MUST | Low |
| Create service accounts + IAM | Infra | MUST | Low |
| Store secrets in Secret Manager | Infra | MUST | Low |
| Write LGD ingestion script (CSV -> BQ) | Backend | MUST | Medium |
| Write JJM ingestion script (CSV -> BQ) | Backend | MUST | Medium |
| Run LGD ingestion for AP | Backend | MUST | Medium |
| Run JJM ingestion for West Godavari + YSR Kadapa | Backend | MUST | Medium |
| Build FastAPI skeleton (health endpoint) | Backend | MUST | Low |
| Dockerize backend + deploy to Cloud Run | Backend | MUST | Medium |
| Build Next.js skeleton (landing page) | Frontend | MUST | Low |
| Dockerize frontend + deploy to Cloud Run | Frontend | MUST | Low |
| Configure Firebase Auth | Frontend | MUST | Low |
| Smoke test: GET /health returns 200 | Both | MUST | Low |

**P0 Exit criterion:** `GET /health` returns 200 from Cloud Run; LGD + JJM tables populated in BigQuery.

---

### P1 -- Vertical Slice (Day 2-3, target: EOD Day 3)

**Goal:** One complete signal -> report chain works end-to-end with synthetic data.

**P1 Tasks:**

| Task | Owner | Priority | Risk |
|------|-------|----------|------|
| Implement `POST /api/signals` (text input) | Backend | MUST | Medium |
| Integrate Gemini extraction (text mode) | Backend | MUST | HIGH |
| Pydantic schema for CivicNeedExtraction | Backend | MUST | Low |
| Geography resolver (location string -> LGD code) | Backend | MUST | Medium |
| LGD historical mapping table + AP 2022 reconciliation | Backend | MUST | HIGH |
| JJM gap calculator (SQL query + arithmetic) | Backend | MUST | Low |
| Priority scorer v1.0 (formula implementation) | Backend | MUST | Low |
| Intelligence Report assembler + BQ storage | Backend | MUST | Medium |
| `GET /api/reports/{id}` endpoint | Backend | MUST | Low |
| Basic report display page (minimal UI) | Frontend | MUST | Low |
| Signal submission form (text only) | Frontend | MUST | Low |
| Synthetic signal seeding script (5-10 signals) | Backend | MUST | Low |
| Evidence ledger write at each step | Backend | MUST | Medium |
| Run end-to-end test: synthetic signal -> full report | Both | MUST | HIGH |

> **REMOVED from P1:** Mission Antyodaya ingestion. It is OPTIONAL and belongs in P2 when the critical slice is proven. JJM + LGD alone is sufficient for P1.

**P1 Exit criterion:** Submit a synthetic Telugu water signal via API; receive a complete Intelligence Report with gap, priority, and provenance trail stored in BigQuery and rendered in browser.

---

### P2 -- Intelligence Expansion (Day 3-4, target: EOD Day 4)

**Goal:** Multiple signals, hotspot aggregation, conflict detection, voice input.

**P2 Tasks:**

| Task | Owner | Priority | Risk |
|------|-------|----------|------|
| Signal aggregation by geography + need | Backend | MUST | Low |
| Hotspot calculation (top N by priority) | Backend | MUST | Low |
| `GET /api/hotspots` endpoint | Backend | MUST | Low |
| Conflict detector (JJM vs citizen claims) | Backend | MUST | Medium |
| Conflict storage + `GET /api/conflicts` | Backend | MUST | Low |
| Voice submission (Gemini audio mode) | Backend | SHOULD | HIGH |
| Audio GCS upload + signed URL flow | Backend | SHOULD | Medium |
| Multilingual test: Telugu + Hindi signals | Backend | SHOULD | Medium |
| `POST /api/signals` audio support | Backend | SHOULD | HIGH |
| Seed 20+ synthetic signals across districts | Backend | MUST | Low |
| YSR Kadapa conflict scenario setup | Backend | MUST | Low |
| Data quality state assignment | Backend | MUST | Low |

**P2 Exit criterion:** Hotspot list shows West Godavari as CRITICAL; YSR Kadapa conflict visible; voice submission works for at least one language.

---

### P3 -- UX and Dashboard (Day 4-5, target: EOD Day 5)

**Goal:** Polished policymaker dashboard with map, report detail, Copilot.

**P3 Tasks:**

| Task | Owner | Priority | Risk |
|------|-------|----------|------|
| Policymaker dashboard layout | Frontend | MUST | Low |
| Google Maps integration (district pins) | Frontend | MUST | Medium |
| Hotspot list view | Frontend | MUST | Low |
| Intelligence Report detail page (full layout) | Frontend | MUST | Low |
| Evidence quality badges | Frontend | MUST | Low |
| Synthetic data badges | Frontend | MUST | Low |
| Conflict alerts on report | Frontend | MUST | Low |
| Copilot chat interface | Frontend | MUST | Medium |
| Copilot backend: `POST /api/copilot` | Backend | MUST | HIGH |
| Gemini function calling implementation | Backend | MUST | HIGH |
| Copilot tool implementations (get_hotspot_details, etc.) | Backend | MUST | Medium |
| Citizen portal (voice + text) | Frontend | MUST | Low |
| Language selector on citizen portal | Frontend | MUST | Low |
| Priority score factor breakdown UI | Frontend | MUST | Low |
| Evidence trail / provenance section | Frontend | MUST | Low |
| Loading states + error states | Frontend | MUST | Low |
| Conflicts review screen | Frontend | SHOULD | Low |
| Dark mode design system applied | Frontend | MUST | Low |

**P3 Exit criterion:** Policymaker can: view map, click hotspot, read report, ask Copilot a question, submit citizen signal -- all in one browser session.

---

### P4 -- Hardening and Demo Prep (Day 5-6, target: EOD Day 5.5)

**Goal:** Secure, stable, demo-ready.

**P4 Tasks:**

| Task | Owner | Priority | Risk |
|------|-------|----------|------|
| Input sanitization and injection prevention | Backend | MUST | Medium |
| Rate limiting on citizen signal endpoint | Backend | MUST | Low |
| Firebase Auth guards on all policymaker routes | Backend + Frontend | MUST | Low |
| CORS configuration (strict origins) | Backend | MUST | Low |
| Security headers on frontend | Frontend | MUST | Low |
| Error handling for all Gemini failures | Backend | MUST | Medium |
| Fallback for geography resolution failures | Backend | MUST | Low |
| Precomputed snapshot tables populated and verified | Backend | MUST | Low |
| Demo fixture data (pre-generated reports) | Backend | MUST | Low |
| Demo mode URL parameter | Frontend | MUST | Low |
| End-to-end smoke test on production deployment | Both | MUST | Low |
| Load test with 50 concurrent requests | Both | SHOULD | Low |
| Verify audio retention lifecycle policy | Infra | MUST | Low |
| Accessibility audit on dashboard | Frontend | SHOULD | Low |

---

### P5 -- Submission (Day 6)

**Goal:** Submit everything on time.

| Task | Owner |
|------|-------|
| Record 3-5 minute demo video | All |
| Create pitch deck (10-12 slides) | All |
| Write 2-3 line brief description | PM |
| Verify GitHub repo is public | All |
| Verify deployed link is live | Infra |
| Submit on hackathon portal | PM |

---

## Critical Path

The critical path items that cannot slip without delaying P1:

1. **LGD + JJM data ingested into BigQuery** (P0, Day 1)
2. **Gemini structured output integration** (P1, Day 2)
3. **LGD historical mapping (AP 2022 reorganization)** (P1, Day 2)
4. **End-to-end signal -> report chain** (P1, Day 3)

Everything else can be cut or deferred if the timeline slips.

---

## What Can Be Cut (in priority order)

| Feature | Cut Impact | Cut Decision |
|---------|-----------|-------------|
| Voice input | Voice demo only; text works | CUT if P1 slips past Day 3 |
| Evidence conflicts screen | Conflict still detectable via API | CUT if P3 slips |
| Copilot | Report still visible; no AI Q&A | CUT if P3 slips significantly |
| Google Maps (use list only) | No map pin viz | CUT if Maps API has issues |
| Mission Antyodaya in report | JJM alone sufficient for gap | CUT if ingestion is complex |
| Historical census population | Population factor from gap_assessments | CUT if Census data is complex |
| Admin panel | Priority weights hardcoded | DEFERRED (not needed for demo) |
| Multilingual voice | English voice works | CUT to one language if time-pressed |

**What CANNOT be cut:**
- End-to-end signal -> report chain (this IS the product)
- Deterministic gap calculation
- Priority score with factor breakdown
- Evidence provenance trail
- Synthetic data labels
- Basic policymaker dashboard
- Cloud Run deployment (live link required)

---

## Dependencies and Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| JJM data in wrong format | Medium | HIGH | Test ingestion on Day 1; have manual CSV prep fallback |
| Gemini audio not supporting Telugu | Medium | Medium | Fall back to English voice or text-only |
| AP 2022 reorganization join failures | Low | HIGH | Build and test historical mapping table before P1 |
| Cloud Run deployment issues | Low | HIGH | Deploy on Day 1 with skeleton; don't wait for full app |
| BigQuery quota exceeded | Very Low | Medium | Use BigQuery sandbox; monitor usage |
| Maps API key domain restriction | Low | Low | Pre-configure authorized domains on Day 1 |
| Firebase Auth OAuth redirect | Low | Medium | Test auth flow on Day 1-2 |

---

*Architecture FINAL FREEZE -- 2026-09-24*
