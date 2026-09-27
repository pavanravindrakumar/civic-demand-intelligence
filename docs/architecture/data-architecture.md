# Data Architecture

> Civic Demand Intelligence & Planning Platform -- Architecture V1
> Last updated: 2026-09-24

---

## 1. Principles

1. **RAW → NORMALIZED → CANONICAL → DERIVED** lifecycle. Original sources are never mutated.
2. LGD numeric codes are the canonical administrative identity for the **active geography version**. An internal stable `geography_id` UUID is the true stable primary key across boundary changes.
3. Source-native identifiers are always preserved alongside canonical codes.
4. Missing data is a first-class state, not a zero.
5. Every derived value carries the calculation version that produced it.
6. Synthetic data carries an `is_synthetic` flag and is never mixed silently with official evidence.
7. No graph database. Relational structure in BigQuery with explicit join tables.
8. Gap arithmetic lives in `gap_assessments`, not in evidence tables. Evidence tables store raw source values only.

---

## 2. BigQuery Dataset Structure

```
project-id.civic_intelligence/
  -- Geography
  lgd_states
  lgd_districts                   (includes centroid_lat, centroid_lng)
  lgd_blocks
  lgd_villages
  geography_versions              (LGD snapshot release tracking)
  geography_boundary_events       (splits, merges, renames -- AP 2022, AP 2025, etc.)
  geography_resolution_log        (all resolution attempts with confidence)

  -- Citizen Signals
  citizen_signals                 (raw parsed signals + provenance)
  civic_needs                     (normalized, deduplicated civic needs)
  need_links                      (many-to-many: signal -> civic need)
  signal_geography_links          (signal -> resolved geography_id)

  -- Evidence (Source)
  evidence_jjm_district           (JJM district-level snapshot)
  evidence_jjm_village            (JJM village-level snapshot -- raw values only)
  evidence_mission_antyodaya      (Mission Antyodaya GP indicators -- OPTIONAL)
  evidence_census_2011            (Census 2011 village directory -- OPTIONAL)

  -- Intelligence
  gap_assessments                 (calculated gap per need + geography)
  priority_assessments            (priority score per gap assessment)
  intelligence_reports            (assembled Civic Intelligence Reports)
  evidence_ledger                 (full provenance trail for every report)
  priority_policy_config          (versioned priority weight configuration)

  -- Precomputed Analytics (replaces Materialized Views)
  snapshot_hotspot_summary        (precomputed for dashboard hotspot list)
  snapshot_district_intelligence  (precomputed per-district report summary)
  snapshot_evidence_quality_index (precomputed evidence quality by geography)

  -- Conflict
  evidence_conflicts              (detected conflicts between sources)

  -- Interventions (Future)
  interventions                   (future: e-GramSwaraj GPDP data)
```

---

## 3. Core Table Schemas

### 3.1 lgd_villages

```sql
CREATE TABLE lgd_villages (
  lgd_state_code        INT64   NOT NULL,
  lgd_district_code     INT64   NOT NULL,
  lgd_block_code        INT64,
  lgd_gp_code           INT64,
  lgd_village_code      INT64   NOT NULL,   -- PRIMARY KEY
  village_name_en       STRING  NOT NULL,
  village_name_local    STRING,
  major_version         INT64,              -- LGD versioning for boundary changes
  minor_version         INT64,
  status                STRING,             -- LIVE / DELETED / MERGED
  effective_from        DATE,
  effective_to          DATE,               -- NULL = currently active
  ingested_at           TIMESTAMP NOT NULL,
  source_snapshot_ref   STRING              -- GCS path to raw LGD CSV
)
PARTITION BY DATE(ingested_at);
```

### 3.2 geography_boundary_events

```sql
-- Replaces lgd_historical_mapping. Generic model for any administrative boundary change.
CREATE TABLE geography_boundary_events (
  event_id              STRING  NOT NULL,   -- UUID
  event_type            STRING  NOT NULL,   -- SPLIT / MERGE / RENAME / REORGANIZATION
  geography_level       STRING  NOT NULL,   -- STATE / DISTRICT / BLOCK / VILLAGE
  old_name              STRING,             -- name before event
  old_lgd_code          INT64,              -- LGD code before event (if known)
  new_lgd_code          INT64,             -- LGD code after event
  new_name              STRING,
  effective_date        DATE    NOT NULL,   -- when the boundary change took effect
  lgd_version_before    STRING,            -- LGD snapshot version before
  lgd_version_after     STRING,            -- LGD snapshot version after
  notes                 STRING,
  source_reference      STRING,             -- e.g. "AP GO Ms No 263 dated 2022-04-04"
  ingested_at           TIMESTAMP NOT NULL
);
-- AP 2022: 13->26 districts loaded as REORGANIZATION events
-- AP 2025: 26->28 districts loaded as REORGANIZATION events
-- All future changes: add rows here, no code changes
```

### 3.3 citizen_signals

```sql
CREATE TABLE citizen_signals (
  signal_id             STRING  NOT NULL,   -- UUID PRIMARY KEY
  idempotency_key       STRING  NOT NULL,   -- hash(source + source_signal_id)
  source                STRING  NOT NULL,   -- WEB_FORM / VOICE / API / SYNTHETIC
  is_synthetic          BOOL    NOT NULL DEFAULT FALSE,
  source_signal_id      STRING,             -- external reference if any
  raw_text              STRING,             -- original text (may be transcribed)
  audio_gcs_ref         STRING,             -- GCS URI if voice input
  detected_language     STRING,             -- BCP-47 language code
  submitted_at          TIMESTAMP NOT NULL,
  ingested_at           TIMESTAMP NOT NULL,
  processing_version    STRING  NOT NULL,   -- version of extraction logic
  extraction_status     STRING  NOT NULL,   -- PENDING / COMPLETED / FAILED
  -- PII notes: no name, phone, email stored; location extracted by Gemini
  submitter_pseudonym   STRING              -- optional pseudonymous session ID
)
PARTITION BY DATE(submitted_at);
```

### 3.4 civic_needs

```sql
CREATE TABLE civic_needs (
  need_id               STRING  NOT NULL,   -- UUID PRIMARY KEY
  canonical_need_type   STRING  NOT NULL,   -- e.g. WATER_SUPPLY_DEFICIT
  need_label_en         STRING  NOT NULL,   -- human-readable: "Drinking Water Access"
  need_description      STRING,
  sector                STRING  NOT NULL,   -- WATER / ROADS / HEALTH / SANITATION
  related_need_ids      ARRAY<STRING>,      -- linked needs (semantic graph -- relational)
  is_composite          BOOL    NOT NULL DEFAULT FALSE,
  first_seen_at         TIMESTAMP,
  last_updated_at       TIMESTAMP,
  processing_version    STRING  NOT NULL
);
```

### 3.5 evidence_jjm_village

```sql
CREATE TABLE evidence_jjm_village (
  evidence_id           STRING  NOT NULL,   -- UUID
  geography_id          STRING,             -- FK -> canonical geography (stable ID)
  lgd_state_code        INT64,
  lgd_district_code     INT64,
  lgd_village_code      INT64,
  source_village_name   STRING,             -- JJM native name (preserved exactly)
  source_district_name  STRING,             -- JJM native district (preserved exactly)
  resolution_status     STRING  NOT NULL,   -- CONFIRMED / PROBABLE / UNRESOLVED
  resolution_confidence FLOAT64,
  -- RAW JJM values only -- no calculated columns in evidence table
  total_households      INT64,              -- as reported in JJM data
  fhtc_households       INT64,              -- Functional Household Tap Connections (as reported)
  -- NOTE: gap_units (total - fhtc) is calculated in gap_assessments, NOT stored here
  quality_affected_flag BOOL,              -- Arsenic/Fluoride/Salinity contamination
  quality_issue_type    STRING,             -- ARSENIC / FLUORIDE / SALINITY / NONE
  data_as_of            DATE    NOT NULL,   -- JJM report date
  source                STRING  NOT NULL DEFAULT 'JJM',
  source_url            STRING,             -- JJM dashboard URL or report reference
  ingested_at           TIMESTAMP NOT NULL,
  snapshot_ref          STRING              -- GCS path to raw extract
)
PARTITION BY DATE(data_as_of);
```

### 3.6 gap_assessments

```sql
CREATE TABLE gap_assessments (
  gap_id                STRING  NOT NULL,   -- UUID PRIMARY KEY
  civic_need_id         STRING  NOT NULL,   -- FK -> civic_needs
  lgd_village_code      INT64,
  lgd_district_code     INT64   NOT NULL,
  lgd_block_code        INT64,
  sector                STRING  NOT NULL,
  gap_type              STRING  NOT NULL,   -- HOUSEHOLD_TAP_CONNECTION (MVP)
  total_units           INT64,              -- total_households
  served_units          INT64,              -- fhtc_households
  gap_units             INT64,              -- unmet_households
  gap_percentage        FLOAT64,           -- gap_units / total_units
  evidence_quality      STRING  NOT NULL,  -- AVAILABLE / PARTIAL / MISSING / CONFLICTING / LOW_CONFIDENCE
  primary_evidence_id   STRING,            -- FK -> evidence_jjm_village
  calculation_version   STRING  NOT NULL,  -- e.g. "gap.water.v1.0"
  calculated_at         TIMESTAMP NOT NULL,
  data_as_of            DATE
)
PARTITION BY DATE(calculated_at);
```

### 3.7 priority_assessments

```sql
CREATE TABLE priority_assessments (
  priority_id               STRING  NOT NULL,   -- UUID PRIMARY KEY
  gap_id                    STRING  NOT NULL,   -- FK -> gap_assessments
  priority_score            FLOAT64 NOT NULL,  -- 0.0 to 1.0
  priority_tier             STRING  NOT NULL,  -- CRITICAL / HIGH / MEDIUM / LOW
  -- Gap Severity factor
  factor_gap_weight         FLOAT64,
  factor_gap_value          FLOAT64,
  factor_gap_contribution   FLOAT64,
  -- Population Impact factor
  factor_pop_weight         FLOAT64,
  factor_pop_value          FLOAT64,
  factor_pop_contribution   FLOAT64,
  -- Validated Citizen Demand factor
  factor_demand_weight      FLOAT64,
  factor_demand_value       FLOAT64,
  factor_demand_contribution FLOAT64,
  -- Urgency / Essentiality factor
  factor_urgency_weight     FLOAT64,
  factor_urgency_value      FLOAT64,
  factor_urgency_contribution FLOAT64,
  -- Evidence Quality factor
  factor_quality_weight     FLOAT64,
  factor_quality_value      FLOAT64,
  factor_quality_contribution FLOAT64,
  -- Raw inputs
  organic_demand_count      INT64,            -- deduplicated, non-synthetic signals
  synthetic_demand_count    INT64,
  demand_saturation_cap     INT64,            -- the cap value used for this calculation
  population_context        INT64,
  -- Versioning (all required)
  priority_policy_version   STRING  NOT NULL, -- e.g. "v1.0.0"
  calculation_version       STRING  NOT NULL, -- e.g. "priority.v1.0"
  calculated_at             TIMESTAMP NOT NULL
)
PARTITION BY DATE(calculated_at);
```

### 3.8 intelligence_reports

```sql
CREATE TABLE intelligence_reports (
  report_id             STRING  NOT NULL,   -- UUID PRIMARY KEY
  report_version        INT64   NOT NULL DEFAULT 1,
  priority_id           STRING  NOT NULL,   -- FK -> priority_assessments
  gap_id                STRING  NOT NULL,   -- FK -> gap_assessments
  civic_need_id         STRING  NOT NULL,   -- FK -> civic_needs
  lgd_district_code     INT64   NOT NULL,
  lgd_village_code      INT64,
  generated_at          TIMESTAMP NOT NULL,
  report_schema_version STRING  NOT NULL,  -- "1.0.0"
  report_json           JSON,              -- Full serialized report (denormalized for display)
  gemini_narrative      STRING,            -- Gemini-generated explanation (labeled AI-generated)
  is_published          BOOL    NOT NULL DEFAULT FALSE,
  conflicts_present     BOOL    NOT NULL DEFAULT FALSE,
  synthetic_signals_present BOOL NOT NULL DEFAULT FALSE
)
PARTITION BY DATE(generated_at);
```

### 3.9 evidence_ledger

```sql
CREATE TABLE evidence_ledger (
  ledger_id             STRING  NOT NULL,
  report_id             STRING  NOT NULL,   -- FK -> intelligence_reports
  step_type             STRING  NOT NULL,   -- SIGNAL_RECEIVED / NEED_EXTRACTED / GEOGRAPHY_RESOLVED / EVIDENCE_QUERIED / GAP_CALCULATED / PRIORITY_CALCULATED / CONFLICT_DETECTED / REPORT_GENERATED
  step_order            INT64   NOT NULL,
  entity_id             STRING,            -- ID of the entity produced at this step
  entity_type           STRING,            -- TABLE name
  source                STRING,
  source_version        STRING,
  data_as_of            DATE,
  processing_version    STRING,
  calculation_version   STRING,
  assumptions           STRING,            -- JSON array of assumption strings
  data_quality          STRING,            -- AVAILABLE / PARTIAL / MISSING / CONFLICTING
  recorded_at           TIMESTAMP NOT NULL
)
PARTITION BY DATE(recorded_at);
```

### 3.10 evidence_conflicts

```sql
CREATE TABLE evidence_conflicts (
  conflict_id           STRING  NOT NULL,
  report_id             STRING,
  evidence_id_a         STRING  NOT NULL,
  evidence_id_b         STRING  NOT NULL,
  source_a              STRING  NOT NULL,
  source_b              STRING  NOT NULL,
  conflict_type         STRING  NOT NULL,  -- VALUE_MISMATCH / DATE_MISMATCH / COVERAGE_MISMATCH
  field_name            STRING  NOT NULL,
  value_a               STRING,
  value_b               STRING,
  data_as_of_a          DATE,
  data_as_of_b          DATE,
  resolution_status     STRING  NOT NULL DEFAULT 'OPEN',  -- OPEN / REVIEWED / DISMISSED
  resolution_note       STRING,
  detected_at           TIMESTAMP NOT NULL
)
PARTITION BY DATE(detected_at);
```

---

## 4. Data Quality States

Every evidence item and gap assessment carries a `evidence_quality` field.

| State | Meaning | UI Treatment |
|-------|---------|-------------|
| AVAILABLE | Full data from authoritative source | Green indicator |
| PARTIAL | Some fields present; others missing | Yellow indicator |
| MISSING | No authoritative data found | Red/grey indicator -- never fill with LLM |
| CONFLICTING | Two or more sources disagree | Orange indicator -- show both sources |
| LOW_CONFIDENCE | Data exists but quality/age is suspect | Yellow indicator with caveat |

---

## 5. Source Classification

| Source | Classification | MVP Role | Gap Feasibility |
|--------|---------------|----------|----------------|
| LGD Bulk CSV | CORE | Geographic identity spine | N/A (identity) |
| JJM District/Village | CORE | Primary gap evidence | HIGH -- arithmetic |
| Mission Antyodaya 2022-23 | SUPPORTING | Development context | MEDIUM -- contextual |
| Census 2011 | CONTEXTUAL | Historical population baseline | LOW -- outdated |
| PMGSY / GeoSadak | FUTURE ADAPTER | Roads sector | LOW in MVP -- needs routing |
| e-GramSwaraj / GPDP | FUTURE ADAPTER | Intervention evidence | LOW in MVP -- scraping risk |
| APSAC WMS | CONTEXTUAL | Visual map overlay only | NONE for backend logic |
| LGD NAPIX API | EXCLUDED (MVP) | Replaced by static CSV | N/A |

---

## 6. Data Ingestion Pipeline

```
GCS Raw Bucket
  lgd/snapshot_YYYYMMDD/states.csv
  lgd/snapshot_YYYYMMDD/districts.csv
  lgd/snapshot_YYYYMMDD/villages.csv
  jjm/snapshot_YYYYMMDD/district_coverage.csv
  jjm/snapshot_YYYYMMDD/village_coverage.csv
  mission_antyodaya/snapshot_YYYYMMDD/gp_indicators.csv
  census2011/village_directory.csv

  -> Source Adapter Scripts (Python)
  -> BigQuery Staging Tables (raw, typed)
  -> Geography Reconciler (LGD code assignment)
  -> BigQuery Canonical Tables
```

**All ingestion scripts are idempotent.** They check `ingested_at` timestamps and skip already-loaded snapshots.

---

## 7. Geographic Join Strategy

All joins route through LGD codes. String-based joins are only used during the initial geography resolution step and the result is cached as an LGD code.

```sql
-- Example: Join JJM village data to canonical LGD
SELECT
  v.lgd_village_code,
  v.village_name_en,
  j.total_households,
  j.fhtc_households,
  j.total_households - j.fhtc_households AS unmet_households
FROM lgd_villages v
JOIN evidence_jjm_village j
  ON v.lgd_village_code = j.lgd_village_code  -- LGD code join -- always numeric
WHERE v.lgd_district_code = 527  -- West Godavari
  AND j.data_as_of = (SELECT MAX(data_as_of) FROM evidence_jjm_village)
```

---

## 8. Synthetic Data Isolation

Synthetic signals MUST:
1. Set `is_synthetic = TRUE` at creation time
2. Never have `is_synthetic` changed to `FALSE`
3. Be visible in all aggregations with a `has_synthetic` warning flag
4. Be excluded from "official demand" calculations when synthetic is toggled off
5. Be shown with `[SYNTHETIC SIGNAL]` badge in all UI views

The `priority_assessments` table includes a `synthetic_demand_count` field separate from `organic_demand_count` to allow policymakers to see the ratio.

---

## 9. Pilot Data Plan (MVP)

For the 6-day MVP, the following data must be loaded into BigQuery before P1:

| Dataset | Scope | Format | Priority |
|---------|-------|--------|---------|
| LGD States/Districts/Blocks/Villages | All India (or AP minimum) | CSV | P0 -- Day 1 |
| Geography Boundary Events (AP 2022 + AP 2025) | AP only | CSV / Manual | P0 -- Day 1 |
| JJM Village Coverage | AP (West Godavari + YSR Kadapa) | CSV extract | P0 -- Day 1 |
| JJM District Coverage | AP | CSV extract | P0 -- Day 1 |
| Mission Antyodaya GP Indicators | AP subset | CSV | **OPTIONAL -- P2 if feasible** |
| Census 2011 Village Directory | AP subset | CSV | **OPTIONAL -- P2 if feasible** |

---

*Architecture V1 -- 2026-09-24*
