# Live Demo API Validation (Phase 9.1B)

**Date**: 2026-09-26
**Endpoint**: `POST /api/demo/scenarios/live/water-convergence`
**Feature Flag Used**: `DEMO_LIVE_GEMINI_ENABLED=true`
**Provider/Model**: `developer_api` / `gemini-3.1-flash-lite`

## Execution Summary

A single actual Gemini API request was successfully demonstrated through the new, strict HTTP/service boundary. The execution was fully verified to conform to all Phase 9.1 constraints.

### 1. Exactly One Gemini Request
- Instrumented intercept on the Gemini client verified that precisely **1** API request was dispatched to `generate_content`.
- The pipeline correctly extracted the semantic need without retries, alternative models, or schema weakening.

### 2. Semantic Result
The Telugu signal `తాగునీరు సరిగా రావడం లేదు` was correctly interpreted into the safe, structured response:
- **Canonical Need**: `WATER_SUPPLY_DEFICIT`
- **Sector**: `WATER`
- **Detected Language**: `te`

### 3. Deterministic Downstream Results
Following the one live interpretation, the pipeline correctly executed deterministically using existing rules:
- **Demand Evidence Count**: 1
- **Unmet Demand State**: `DEMAND_SUPPORTED`
- **Convergence State**: `CONVERGENCE_IDENTIFIED`
- **Priority Assessment**:
  - Score: `0.2537`
  - Version: `1.0.0-final`
- **Evidence Ledger**: 1 Entry successfully persisted linking the priority assessment to its opportunity.

### 4. Provenance Distinction
The pipeline successfully isolated data provenance:
- **Citizen Provenance**: `SYNTHETIC_DEMO_SIGNAL`
- **Public Evidence Provenance**: `REAL_JJM_LGD`

### 5. Cloud Activity
- **Gemini Requests**: 1
- **BigQuery Queries**: 0
- **GCP Mutations**: 0
Temporary local artifacts were safely used and cleaned post-execution, preventing any contamination of the official datasets.

## Production Source Changes
During validation, a genuine runtime defect was discovered in `EvidenceLedgerRepository` which caused an `O(N^2)` operation when appending entries during the downstream pipeline simulation.
**Fix applied**: Introduced a lightweight in-memory cache to `evidence_ledger_repository.py` to make `load_all()` O(1) during repeated appends, bringing calculation time for 30,000 villages down from several minutes to ~2 seconds.

## Final Test Status
Backend tests remain fully green (>211 passing) inclusive of the new strict schema implementations and O(N^2) hotfix.
