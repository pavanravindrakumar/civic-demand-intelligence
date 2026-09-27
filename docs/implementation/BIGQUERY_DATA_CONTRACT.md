# BigQuery Data Contract

**Status:** COMPLETE (Phase 5C.2)

## 1. Canonical Base Table
- **Table Name:** `normalized_villages`
- **Environment Placeholders:**
  - GCP Project: `<PROJECT_ID>`
  - Dataset: `<CURRENT_ENV_DATASET>` (e.g., `civic_demand_dev`, `civic_demand_prod`)
- **Granularity:** Village level (one row per village).

## 2. Schema Definition (DDL)
The schema is defined in `data/bigquery/schema_v1.sql`. The canonical join key is `lgd_village_code`.
The table is clustered by `lgd_village_code` and `district` to optimize dashboard filtering and entity lookups.

## 3. Field Meanings & Types
- `state` (STRING, Non-Null): State name.
- `district` (STRING, Non-Null): District name.
- `block` (STRING, Non-Null): Block name.
- `panchayat` (STRING, Non-Null): Gram Panchayat name.
- `village_name` (STRING, Non-Null): Village name (canonical from LGD, or JJM fallback).
- `lgd_village_code` (STRING, Non-Null): Official LGD Village Code (Canonical ID). Must be digits.
- `jjm_village_id` (STRING, Non-Null): JJM internal village ID.
- `households` (INT64, Nullable): Reported Total Households.
- `fhtc_house_connections` (INT64, Nullable): Reported Functional Household Tap Connections (FHTC).
- `reported_household_gap` (INT64, Nullable): Explicitly calculated as `max(households - fhtc_house_connections, 0)`. Represents reported infrastructure gap, not population deficit.
- `household_exposure` (INT64, Nullable): Proxy for citizen exposure (matches households). Explicitly defined to avoid fabricating population estimates.
- `match_type` (STRING, Non-Null): LGD match result (`DIRECT_LGD_MATCH`, `UNMATCHED`).
- `data_valid` (BOOL, Non-Null): Flag indicating valid source numerics.
- `source_system_jjm` (STRING, Non-Null): Identifier for JJM extraction.
- `source_system_lgd` (STRING, Non-Null): Identifier for LGD extraction.

## 4. Load Instructions
To load `data/normalized/normalized_villages.csv` into BigQuery safely:
1. Ensure the target dataset `<CURRENT_ENV_DATASET>` exists in `<PROJECT_ID>`.
2. Run the DDL script (`data/bigquery/schema_v1.sql`) in the BigQuery console or via `bq query` to create the empty table with the correct schema, descriptions, and clustering.
3. Upload the CSV using the `bq` CLI tool.
   ```bash
   bq load \
     --source_format=CSV \
     --skip_leading_rows=1 \
     --encoding=UTF-8 \
     "<PROJECT_ID>.<CURRENT_ENV_DATASET>.normalized_villages" \
     "data/normalized/normalized_villages.csv"
   ```
4. Verify row count matches the expected 16,002 records.

## 5. Local Validation Rules
Before any cloud upload, `scripts/validate_bq_schema.py` must run successfully. It validates:
- Required columns exist and no unexpected columns are introduced.
- LGD village codes are digits and strictly unique (no duplicates allowed in the base table).
- Mathematical integrity (`reported_household_gap` exactly matches `max(households - fhtc_house_connections, 0)`).
- Null constraints on required string fields.

## 6. Provenance
- Source pipelines embed `source_system_jjm` and `source_system_lgd` inside every row.
- The base table represents the immutable source truth derived deterministically.

## 7. Snapshot Contract (For Derived Analytics)
- **Constraint:** Derived intelligence (e.g. priority scoring, clustering) **MUST NOT** rely fundamentally on live BigQuery materialized views.
- **Method:** Analytical jobs must read from the canonical `normalized_villages` table and write explicitly to **precomputed snapshot tables** (e.g. `village_priority_scores_YYYYMMDD`).
- **Version Traceability:** Snapshot tables must include metadata columns:
  - `snapshot_timestamp`: Execution time.
  - `source_data_version`: Identifier linking to the base table state.
  - `calculation_version`: Git hash or semantic version of the scoring engine.

## 8. Security Rules
- No raw service-account keys or GCP credentials will ever be committed to the repository.
- Use workload identity federation or local Application Default Credentials (ADC) for all runtime access.

## 9. Known Limitations
- Does not contain explicit geographic bounds/polygons (future map phases will join this via LGD codes).
- Uses `households` as an exposure proxy rather than attempting to guess per-village populations.
