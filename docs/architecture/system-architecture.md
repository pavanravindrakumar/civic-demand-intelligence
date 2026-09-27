# System Architecture

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. System Boundary

The platform is an **intelligence layer** between citizen demand and development planning.

**Inside the system boundary:**
- Citizen signal ingestion (text, voice, multilingual)
- AI-powered civic need extraction and normalization
- Administrative geography resolution (LGD)
- Public evidence querying and storage
- Deterministic gap and priority calculation
- Civic Intelligence Report generation
- Policymaker dashboard and AI Copilot

**Outside the system boundary:**
- Government portal administration
- Actual delivery of development projects
- Policy decision-making (humans remain responsible)
- Live government API management
- Payment or procurement systems

---

## 2. System Overview Diagram

```mermaid
graph TB
    subgraph "Citizen Input Layer"
        CT[Citizen Text Input]
        CV[Citizen Voice Input]
        CM[Messaging Channel - Future]
    end

    subgraph "AI Extraction Layer"
        GE[Gemini 2.0 Flash\nCivic Need Extractor]
        SO[Structured Output\nPydantic Validation]
    end

    subgraph "Resolution Layer"
        ER[Entity Resolver\nLGD Lookup]
        GR[Geography Reconciler\nName -> LGD Code]
    end

    subgraph "Evidence Layer"
        BQ[(BigQuery\nCanonical Store)]
        LGD_T[LGD Table]
        JJM_T[JJM Table]
        MA_T[Mission Antyodaya Table]
        CEN_T[Census 2011 Table]
    end

    subgraph "Intelligence Layer"
        GAP[Gap Calculator\nDeterministic SQL]
        PRI[Priority Scorer\nDeterministic Formula]
        CON[Conflict Detector]
        REP[Report Generator]
    end

    subgraph "Presentation Layer"
        DASH[Policymaker Dashboard]
        MAP[Map View]
        COP[AI Copilot\nGrounded Explanation]
    end

    subgraph "Storage"
        GCS[Cloud Storage\nRaw Snapshots + Audio]
    end

    CT --> GE
    CV --> GCS
    GCS --> GE
    GE --> SO
    SO --> ER
    ER --> GR
    GR --> BQ
    BQ --> LGD_T
    BQ --> JJM_T
    BQ --> MA_T
    BQ --> CEN_T
    LGD_T --> GAP
    JJM_T --> GAP
    MA_T --> GAP
    GAP --> PRI
    GAP --> CON
    PRI --> REP
    CON --> REP
    REP --> DASH
    DASH --> MAP
    DASH --> COP
    COP --> GE
```

---

## 3. End-to-End Signal Flow

```mermaid
sequenceDiagram
    participant C as Citizen
    participant API as FastAPI Backend
    participant GEM as Gemini 2.0 Flash
    participant BQ as BigQuery
    participant DASH as Dashboard

    C->>API: POST /signals (text or audio)
    API->>API: Sanitize input (strip PII, injection checks)
    API->>GCS: Store audio if voice (get reference URL)
    API->>GEM: Extract civic need (structured schema)
    GEM-->>API: CivicNeedExtraction JSON (validated by Pydantic)
    API->>BQ: Resolve location -> LGD code (deterministic lookup)
    BQ-->>API: lgd_village_code, lgd_district_code, resolution_status
    API->>BQ: Aggregate signals by need + geography
    API->>BQ: Query JJM evidence for resolved geography
    BQ-->>API: total_hh, fhtc_hh, data_as_of
    API->>API: Calculate gap (total_hh - fhtc_hh)
    API->>API: Calculate priority score (versioned formula)
    API->>API: Detect conflicts with existing evidence
    API->>BQ: Store civic need, gap, priority, report
    API-->>DASH: Civic Intelligence Report JSON
    DASH->>DASH: Render report with evidence, confidence, conflicts
    DASH->>GEM: Copilot query (grounded explanation request)
    GEM-->>DASH: Narrative explanation (read-only tool results)
```

---

## 4. AI vs Deterministic Boundary

This is the most critical architectural boundary in the system.

```mermaid
graph LR
    subgraph "Gemini Does"
        A1[Understand multilingual text]
        A2[Understand voice/audio]
        A3[Classify civic need category]
        A4[Extract location expression]
        A5[Extract urgency signals]
        A6[Normalize need synonyms]
        A7[Explain report to policymaker]
        A8[Respond to Copilot queries]
        A9[Propose tool calls for read-only functions]
    end

    subgraph "Deterministic Code Does"
        B1[Resolve location -> LGD code]
        B2[Query JJM evidence]
        B3[Calculate gap arithmetic]
        B4[Calculate priority score]
        B5[Detect evidence conflicts]
        B6[Validate Gemini structured output]
        B7[Assign data quality states]
        B8[Track provenance]
        B9[Authorize Copilot tool calls]
        B10[Execute read-only Copilot tools]
        B11[Detect duplicate signals]
        B12[Aggregate demand counts]
    end

    NEVER[NEVER CROSS]
    A3 -.->|cannot| B3
    A4 -.->|cannot| B1
    A7 -.->|cannot| B4
```

**Key rule:** Gemini produces structured JSON that the backend validates. The backend then runs all calculations. Gemini is shown the results and asked to explain them -- it never generates them.

---

## 5. Data Lifecycle

```mermaid
graph LR
    R[RAW\nOriginal source files\nGCS bucket]
    N[NORMALIZED\nCleaned, typed\nBigQuery staging tables]
    CA[CANONICAL\nLGD-resolved\nBigQuery canonical tables]
    D[DERIVED\nGap, priority, report\nBigQuery derived tables]
    PL[PROVENANCE LEDGER\nEvery derivation step\nBigQuery evidence_ledger]

    R -->|Source adapter scripts| N
    N -->|Geography reconciler| CA
    CA -->|Gap calculator + Priority scorer| D
    D -->|Report generator| PL
    R -.->|Snapshot preserved| R
```

---

## 6. Geography Reconciliation

```mermaid
graph TD
    INPUT[Raw location string\ne.g. Bhimavaram, or\nma voila village]
    EXTRACT[Gemini extracts\nlocation_expression]
    FUZZY[Backend fuzzy match\nagainst LGD village names\nBigQuery LIKE / Levenshtein]
    CONFIRM[Match confidence check\n>= 0.85 = CONFIRMED\n0.60-0.85 = PROBABLE\n< 0.60 = UNRESOLVED]
    LGD_REC[LGD record stored\nwith resolution_status\nand resolution_confidence]
    FAIL[Signal stored as\nresolution_status = UNRESOLVED\nExposed in UI]

    INPUT --> EXTRACT
    EXTRACT --> FUZZY
    FUZZY --> CONFIRM
    CONFIRM -->|High confidence| LGD_REC
    CONFIRM -->|Low confidence| FAIL
```

**The 2022 AP reorganization is handled** by a `lgd_historical_mapping` table that bridges pre-2022 district names to post-2022 LGD codes. This is not a GIS problem -- it is a name/code reconciliation table.

---

## 7. Gap to Priority Pipeline

```mermaid
graph TD
    SIG[Citizen Signals\nfor a geography + need]
    DEMAND[Demand Count\nN signals in last 30/90 days]
    EVIDENCE[JJM Evidence\ntotal_hh, fhtc_hh]
    GAP[Gap Calculation\nunmet = total_hh - fhtc_hh\ngap_pct = unmet / total_hh]
    POP[Population Context\nCensus 2011 village pop\nLabeled as historical]
    QUALITY[Evidence Quality\nAVAILABLE / PARTIAL /\nMISSING / CONFLICTING]
    PRIORITY[Priority Score\nWeighted formula v1.0\nAll factors shown]
    REPORT[Civic Intelligence Report]

    SIG --> DEMAND
    EVIDENCE --> GAP
    GAP --> PRIORITY
    DEMAND --> PRIORITY
    POP --> PRIORITY
    QUALITY --> PRIORITY
    PRIORITY --> REPORT
    DEMAND --> REPORT
    GAP --> REPORT
    EVIDENCE --> REPORT
```

**Priority Formula v1.0:**
```
priority_score = (
  w_gap     * gap_pct +
  w_demand  * normalized_demand_count +
  w_pop     * normalized_population_impact +
  w_quality * evidence_quality_multiplier
)

Where:
  w_gap     = 0.40  (biggest weight -- actual infrastructure deficit)
  w_demand  = 0.30  (citizen demand signal strength)
  w_pop     = 0.20  (population affected)
  w_quality = 0.10  (evidence quality bonus/penalty)

All weights sum to 1.0 and are configurable via admin interface.
Formula version tracked as priority_schema_version = "1.0.0"
```

**What this formula CANNOT include in MVP (data not yet available):**
- Urgency from government declarations (future)
- Existing intervention coverage (future -- e-GramSwaraj)
- Accessibility penalty (future)

---

## 8. Civic Intelligence Report Structure

The report is the central user-facing output. It contains:

| Section | Content | Source |
|---------|---------|--------|
| Need | Civic need category + description | Gemini extraction + normalization |
| Location | District + Block + Village + LGD codes | LGD resolution |
| Citizen Demand | Signal count + trend | Aggregated signals |
| Population Context | Village/block population | Census 2011 (labeled historical) |
| Infrastructure State | Households with tap water | JJM evidence |
| Gap | Unmet households + gap percentage | Deterministic calculation |
| Priority | Score + factor breakdown | Deterministic formula |
| Evidence Quality | AVAILABLE / PARTIAL / CONFLICTING | Data quality assessment |
| Conflicts | Any conflicting sources | Conflict detector |
| Recommendation | Narrative guidance | Gemini (grounded on above) |
| Provenance | Full evidence trail | Evidence ledger |

---

## 9. Country / Sector / Source Adapter Pattern

The platform is designed for extensibility without implementing extensions now.

```mermaid
graph TB
    CORE[Civic Intelligence Core\nCanonical model + Intelligence engine]

    subgraph "Country Adapters"
        INDIA[India Adapter\nLGD + JJM + Mission Antyodaya]
        FUTURE_C[Future Country\nEquivalent geography identity]
    end

    subgraph "Sector Adapters"
        WATER[Water Adapter\nJJM gap logic]
        ROADS[Roads Adapter - Future\nPMGSY gap logic]
        HEALTH[Health Adapter - Future\nHFM gap logic]
    end

    subgraph "Source Adapters"
        LGD_A[LGD Source Adapter\nBulk CSV ingestion]
        JJM_A[JJM Source Adapter\nDistrict/Village extract]
        MA_A[Mission Antyodaya Adapter\nGP CSV ingestion]
    end

    INDIA --> CORE
    FUTURE_C -.->|Future| CORE
    WATER --> INDIA
    ROADS -.->|Future| INDIA
    HEALTH -.->|Future| INDIA
    LGD_A --> INDIA
    JJM_A --> WATER
    MA_A --> INDIA
```

**Adapter contracts:** Each adapter must implement:
- `ingest_source(snapshot_ref) -> NormalizedDataset`
- `resolve_geography(source_id) -> CanonicalGeography`
- `calculate_gap(canonical_geography) -> GapAssessment`

These are **interface definitions only** -- not implemented until the adapter is needed.

---

## 10. Deployment Architecture (Summary)

See [deployment-architecture.md](deployment-architecture.md) for full detail.

```
Cloud Run (backend)  <-->  BigQuery (data)
       |                       ^
       v                       |
Cloud Storage (raw)    Cloud Run (frontend)
       |                       |
Secret Manager         Firebase Auth
       |                       |
Gemini API             Google Maps API
```

---

## 11. Architectural Decisions Summary

All significant decisions are documented in [docs/adr/](../adr/).

| Decision | Choice | Key Reason |
|----------|--------|-----------|
| Geography identity | LGD numeric codes | Immutable, national, tabular |
| Deep sector | Water / JJM | Arithmetic gap; highest data fidelity |
| Analytical database | BigQuery | Serverless SQL analytics; no ops overhead |
| Spatial strategy | Tabular joins only (MVP) | No GIS risk on 6-day timeline |
| AI role | Extract + explain only | Prevents hallucination of official stats |
| Deployment | Cloud Run (monorepo, 2 services) | Simplest credible serverless path |
| Auth | Firebase Authentication | Managed; Google provider |
| Maps | Google Maps JS API (pins) | No advanced GIS needed for MVP |
| Data ingestion | Static CSV snapshots to BQ | Eliminates live API dependency |
| Synthetic data | Isolated with `is_synthetic` flag | Evidence integrity |

---

*Architecture V1 -- 2026-09-24*
