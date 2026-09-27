# Decision Summary

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

All significant architectural decisions in one place. Full ADRs in [docs/adr/](../adr/).

---

## Required Architectural Questions -- Answers

### 1. What is the system boundary?
The platform is an **intelligence layer**. It ingests citizen signals and public evidence, and produces Intelligence Reports and Copilot answers for policymakers. It does not manage project delivery, budget approval, or government administration.

### 2. What is the canonical data model?
Five core canonical entities: `GeographicUnit` (LGD), `CitizenSignal`, `CivicNeed`, `EvidenceItem`, and `IntelligenceReport`. These are implemented as BigQuery tables (see [data-architecture.md](data-architecture.md)).

### 3. What is the geography model?
LGD numeric codes are the canonical geographic identity. Administrative hierarchy: State -> District -> Block -> Village -> Gram Panchayat. Source-native IDs are preserved in separate columns. Administrative geography and spatial geometry are treated as separate concerns (spatial is optional and preprocessed).

### 4. How are external IDs reconciled?
Source-native identifiers (e.g., JJM village name, Census location code) are stored alongside the resolved LGD code. Resolution confidence and status are explicit fields. A `lgd_historical_mapping` table handles the 2022 AP reorganization. Resolution is deterministic code, not LLM.

### 5. Which data sources are CORE?
- LGD (geographic identity backbone)
- JJM (primary gap evidence)

### 6. Which are SUPPORTING?
- Mission Antyodaya 2022-23 (development context, GP indicators)
- Census 2011 (population baseline -- labeled as historical)

### 7. Which are CONTEXTUAL?
- APSAC WMS (map overlay only -- not backend logic)
- PMGSY (macro-level road context -- future sector)

### 8. Which remain FUTURE ADAPTERS?
- PMGSY / GeoSadak (Roads sector)
- e-GramSwaraj / GPDP (Intervention evidence)
- NAPIX live API (replaced by static CSV in MVP)
- Health facility datasets
- Non-India geographic identity systems

### 9. What is the actual deep-sector strategy?
**Water and Sanitation / Jal Jeevan Mission.** Reason: Only sector where the gap is arithmetic (total_hh - fhtc_hh), not spatial. Highest data fidelity. Strongest JJM data completeness for AP. Roads require spatial network analysis -- infeasible on 6-day timeline. See ADR-002 and the Gemini research comparison table.

### 10. What is the actual MVP vertical slice?
Text/voice citizen signal (AP, water need) -> Gemini extraction -> LGD resolution -> JJM gap calculation -> Priority score -> Intelligence Report in dashboard. Demo uses West Godavari (CRITICAL) and YSR Kadapa (conflict detection).

### 11. What belongs in BigQuery?
All canonical, derived, and evidence data. Relational analytics at scale. All intelligence calculations.

### 12. What belongs in object storage?
Raw source CSV snapshots (LGD, JJM, Mission Antyodaya CSVs). Citizen audio files (with 24h TTL).

### 13. What requires transactional storage, if anything?
No. BigQuery handles all analytics. The `citizen_signals` table uses `idempotency_key` to handle duplicates. No ACID transaction requirement identified for MVP.

### 14. How does Gemini interact with the backend?
Two modes: (a) Extraction mode -- backend calls Gemini with citizen text/audio + structured schema; Gemini returns JSON; backend validates with Pydantic; (b) Copilot mode -- backend passes Gemini a question + tool declarations; Gemini proposes tool calls; backend validates + executes read-only BQ queries; results returned to Gemini for grounded narrative.

### 15. How are structured outputs validated?
Pydantic v2 `model_validate_json()` on every Gemini response. `response_schema` parameter enforces JSON schema at the API level. Validation failures trigger one retry, then store as FAILED.

### 16. How are conflicts represented?
`evidence_conflicts` BigQuery table. Conflict stores both source A and source B with their native values, data_as_of dates, and conflict type. Resolution status is OPEN until a human reviewer acts. Conflicts are exposed in the Intelligence Report and the conflicts dashboard screen.

### 17. How is missing evidence represented?
`evidence_quality` field in `gap_assessments` and `evidence_jjm_village` tables. Valid states: AVAILABLE, PARTIAL, MISSING, CONFLICTING, LOW_CONFIDENCE. Missing is never silently converted to zero. Priority formula includes an evidence quality factor that penalizes MISSING and PARTIAL states.

### 18. How is synthetic data isolated?
`is_synthetic = TRUE` flag on `citizen_signals`. Aggregation queries default to `WHERE is_synthetic = FALSE`. Priority table has separate `synthetic_demand_count` field. UI shows `[SYNTHETIC]` badge on every instance. Never mixed into the evidence ledger without the flag.

### 19. How is the priority score calculated?
Deterministic formula v1.0.0: weighted sum of gap_pct (40%), normalized_demand_count (30%), normalized_population_impact (20%), evidence_quality_multiplier (10%). All factor values and weights stored in `priority_assessments` table. Gemini never calculates this.

### 20. How is provenance preserved?
`evidence_ledger` table records every step in the intelligence pipeline with: step_type, entity_id, source, data_as_of, processing_version, calculation_version, and assumptions. Every Intelligence Report references a chain of ledger entries from signal receipt to report generation.

### 21. How is the Copilot secured?
Tool allowlist (hard-coded), typed Pydantic argument schemas, no freeform SQL, read-only BigQuery queries, rate limiting (20 queries/user/hour), user pseudonym logging, Gemini session context isolated per policymaker session.

### 22. How is voice handled?
Citizen audio uploaded to Cloud Storage. GCS URI passed to Gemini 2.0 Flash as multimodal input. No separate STT pipeline. Audio auto-deleted after 24 hours via GCS lifecycle rule. No personal linkage preserved.

### 23. How is multilingual support handled?
Gemini extracts civic need from native language text/audio without pre-translation. `detected_language` (BCP-47) stored on signal. UI language selector on citizen portal for input preference. Dashboard in English (policymaker context).

### 24. How much spatial functionality is actually necessary?
Minimum: district centroid lat/lng for map pins (via Geocoding API or hardcoded for pilot districts). Optional: preprocessed district boundary GeoJSON overlaid on Maps. NOT needed: spatial intersection queries, PostGIS, WFS/WMS backend processing, network routing analysis. Map is contextual -- the intelligence product is the report, not the map.

### 25. How is deployment structured?
Two Cloud Run services (backend FastAPI, frontend Next.js) in asia-south1. BigQuery + Cloud Storage + Firebase Auth + Secret Manager as supporting managed services. No Kubernetes, no message queues, no microservices.

### 26. What happens when government data is unavailable?
Evidence quality set to MISSING or PARTIAL. Report generated with available data and explicit caveat. Priority formula uses evidence_quality_multiplier to reduce score for poor evidence. Report prominently shows "No official data available -- based on citizen demand signals only."

### 27. What happens when Gemini fails?
Citizen signal stored in BQ with `extraction_status = PENDING`. Retry queue (simple scheduled Cloud Run job). User sees "Your request has been saved and is being processed." Gap/priority calculations from pre-existing evidence still available in dashboard.

### 28. What happens when geography cannot be resolved?
Signal stored with `resolution_status = UNRESOLVED`. Exposed in dashboard admin view. No gap calculation attempted (would be meaningless). Signal still counted in unresolved demand queue. Policymakers can see there is demand that cannot be localized.

### 29. What happens when evidence conflicts?
Both sources preserved in `evidence_conflicts`. Report shows conflict alert. Copilot can explain the conflict via `show_evidence_conflict` tool. Resolution status set to OPEN. Priority calculation uses the more conservative (worse-case) evidence value and notes the conflict. No silent averaging.

### 30. What happens when data is incomplete?
`evidence_quality = PARTIAL`. Report shows "Partial data -- some fields unavailable." Priority formula applies a quality penalty. Never fill missing fields with LLM estimates.

### 31. How will the system extend to another sector?
Implement a new Sector Adapter with: (a) `need_type` entries added to the civic need allowlist, (b) a new evidence table (e.g., `evidence_pmgsy_village`), (c) a new gap calculation function, (d) the `sector` field on gap_assessments routes to the correct calculator. No core model changes required.

### 32. How will the system extend to another country?
Implement a Country Adapter: (a) new geographic identity table (e.g., `lgd_equivalent_country_x`), (b) new source adapter for that country's data, (c) geographic resolution logic for that country's naming conventions, (d) the `civic_intelligence_core` remains unchanged. Country-specific sector adapters plug in identically.

---

## Technology Evaluation

### BigQuery vs PostgreSQL

BigQuery chosen because:
- No operational overhead (serverless)
- Native analytics at scale (critical for hotspot aggregations across large LGD tables)
- Partitioned tables for efficient date-range queries
- Free sandbox tier sufficient for MVP
- Cloud Run connects without VPC complexity

PostgreSQL considered for:
- Transactional guarantees (not needed -- no ACID requirements identified)
- More familiar for some developers
- Rejected: operational overhead; requires Cloud SQL setup and maintenance

### Cloud Run vs Cloud Functions vs GKE

Cloud Run chosen because:
- Containerized -- supports both Python backend and Node.js frontend
- Scales to zero (cost)
- Simple deploy (one Docker image per service)
- No Kubernetes management overhead
- Sufficient latency for demo use case

### Firebase Auth vs Custom Auth vs IAP

Firebase Auth chosen because:
- Managed Google OAuth
- Easy Next.js integration
- No custom auth server
- Custom claims support for role-based access
- Free tier sufficient

### Google Maps vs OpenStreetMap

Google Maps chosen because:
- Required by challenge (Google technologies preferred)
- Geocoding API for district centroid lookup
- JS Maps API well-documented

### Gemini Multimodal Audio vs Google Speech-to-Text

Gemini multimodal chosen because:
- Single API call instead of two
- Handles multilingual audio without pre-configuration
- Simpler implementation (critical for 6-day timeline)
- No STT language model management

Risk: Audio quality for regional Indian languages needs verification. Fallback is text submission.

---

## Self-Adversarial Review

### 1. Biggest single point of failure
Gemini API availability. If Gemini is down or rate-limited during the demo, new extractions fail. Mitigation: pre-generated demo fixtures.

### 2. Over-engineered?
The `evidence_ledger` table may be more detailed than needed for the MVP demo. However, it is what makes the provenance story credible to judges, so it stays. The sector/country adapter pattern documentation is conceptual only -- no actual interfaces to implement, so cost is zero.

### 3. What can be removed?
- The `intervention` schema can be fully deferred (no data source in MVP)
- The `need_links` (linked needs) table can be deferred -- no real use case in MVP
- `compare_policy_weights` Copilot tool can be deferred

### 4. Weakest research assumption
That JJM data is directly joinable to LGD codes with only name normalization. The AP 2022 reorganization created structural mismatches. If the historical mapping table is incomplete, multiple AP districts will have `UNRESOLVED` geography status. This needs Day 1 validation.

### 5. Where can the LLM hallucinate?
- Copilot mode: Gemini could confuse data from one report with another if context window is poorly managed. Mitigation: pass only the specific report as context.
- Extraction mode: Gemini could infer a need type that is not on the allowlist (but schema prevents this).
- Narrative generation: Gemini could quote statistics not in the provided tool results. Mitigation: explicit system prompt instruction to cite only provided data.

### 6. Where can source reconciliation fail?
AP 2022 district reorganization. Villages split between old and new districts may appear in JJM data under old district names. If the historical mapping table is incomplete, these villages will be `UNRESOLVED`.

### 7. Where can provenance break?
If a batch ingestion script runs without properly setting `data_as_of` and `ingested_at` on every row. Mitigation: make these required NOT NULL fields with script-level assertions.

### 8. Where can synthetic data contaminate real evidence?
Only if `is_synthetic` defaults to `FALSE` for test data. Mitigation: development environment defaults all signals to `is_synthetic = TRUE`. Production environment defaults to `FALSE`. Environment variable controls this.

### 9. Which external service can break the demo?
Gemini API (if quota exceeded or down). Maps API (if domain not authorized). Firebase Auth (if OAuth redirect misconfigured).

### 10. Which component consumes the most development time?
LGD geography resolver + historical mapping (AP 2022). This is the most technically uncertain component because it requires data investigation alongside implementation.

### 11. What should absolutely be deferred?
- e-GramSwaraj intervention data
- PMGSY roads sector
- Multi-country support
- Predictive analytics
- Admin weight configuration UI
- Accessibility audit (WCAG full compliance)

### 12. What must never be sacrificed?
- End-to-end signal -> report chain
- Deterministic gap calculation (never LLM)
- Priority score factor breakdown (transparency is the product)
- Evidence provenance trail
- Synthetic data labels
- Gemini-result/Official-evidence visual separation

### 13. Does the MVP feel complete without deferred features?
Yes. The core product promise -- citizen signal becomes evidence-backed priority with transparent reasoning -- is fully deliverable without roads, interventions, or multi-country support.

### 14. Could another engineer implement from this blueprint?
Yes, with the following documents: system-architecture.md, data-architecture.md, ai-architecture.md, implementation-plan.md, and the five data contracts. The canonical data model and Gemini schemas are specific enough to begin implementation immediately.

---

*Architecture V1 -- 2026-09-24*
