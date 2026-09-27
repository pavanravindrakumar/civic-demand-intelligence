# Data Readiness Gate

> Civic Demand Intelligence & Planning Platform
> Status: **REQUIRED BEFORE UI IMPLEMENTATION**

Before starting work on the backend API endpoints or frontend UI, the engineering team MUST pass this deterministic data validation gate. This prevents silent data drop-offs and ensures the foundation is solid.

## 1. Objective
Verify the integrity, match rate, and quality of the baseline datasets (LGD Geography and JJM Evidence) before application code relies on them.

## 2. Validation Execution
Run a SQL-based data validation script (`scripts/validate_data_readiness.sql`) or a Python script that outputs the following exact metrics.

Do NOT silently discard unmatched records. All anomalies must be logged.

## 3. Required Metrics Report

The validation script must produce a report containing:

### A. Geography (LGD) Base
- **Total LGD Villages Loaded:** `[COUNT]`
- **Geography Version Active:** `[VERSION_STRING]` (e.g., "LGD-2025-01")
- **Duplicate Geography IDs:** `[COUNT]` (MUST BE 0)

### B. Evidence (JJM) Base
- **Total JJM Rows Ingested:** `[COUNT]`
- **Source Vintage (Data As Of):** `[DATE]`
- **Duplicate Evidence IDs:** `[COUNT]` (MUST BE 0)

### C. Join Strategy & Match Rate
*Join strategy: `evidence_jjm_village.source_village_name` -> fuzzy match -> `lgd_villages.source_native_name` -> `geography_id`*

- **Matched JJM Rows:** `[COUNT]`
- **Unmatched JJM Rows:** `[COUNT]`
- **Overall Match Percentage:** `[PERCENTAGE]%` (Target > 90% for AP pilot)
- **Top 10 Unmatched Records:** `[LIST]` (for manual inspection/mapping)

### D. Data Quality & Missing Data
- **JJM Rows with NULL `total_households`:** `[COUNT]`
- **JJM Rows with NULL `fhtc_households`:** `[COUNT]`
- **Invalid Numeric Values (`fhtc` > `total`):** `[COUNT]` (MUST BE 0)
- **Rows where `resolution_status = UNRESOLVED`:** `[COUNT]`

## 4. Acceptance Criteria
The UI and Copilot implementation phases are **BLOCKED** until:
1. Match Percentage > 90% for the pilot districts (West Godavari, YSR Kadapa).
2. Invalid Numeric Values = 0.
3. Duplicate IDs = 0.
4. The Precomputed Snapshot refresh job runs successfully against this validated data.

---
*Implementation Plan - Data Readiness Gate*
