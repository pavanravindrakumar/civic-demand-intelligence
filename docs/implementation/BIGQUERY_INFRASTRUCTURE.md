# BigQuery Infrastructure Record

## Dataset Provisioning

- **Project ID**: `civic-intelligence-hackathon`
- **Dataset Name**: `civic_intelligence`
- **Region**: `asia-south1` (as specified in architecture topology)
- **Status**: CREATED (Verified)
- **Timestamp**: 2026-09-24T23:59:01Z
- **Data Contract Version**: v1 (from `BIGQUERY_DATA_CONTRACT.md`)

## Canonical Base Table Load (Phase 5C.3C)

- **Source Snapshot**: `data/normalized/normalized_villages.csv` (Acquired government JJM/LGD snapshot, NOT a live API feed).
- **Destination Table**: `civic-intelligence-hackathon.civic_intelligence.normalized_villages`
- **Load Method**: `bq load` directly using explicit schema `schema_v1.sql`. No staging/GCS bucket used.
- **Provenance Preserved**: Yes (`source_system_jjm`, `source_system_lgd` mapped to all rows).
- **Validation**:
  - Status: SUCCESS
  - Loaded Rows: 16,002
  - Distinct LGD Codes: 16,002
  - Reported Household Gap Matches: 2,291,495 (0 arithmetic violations)
