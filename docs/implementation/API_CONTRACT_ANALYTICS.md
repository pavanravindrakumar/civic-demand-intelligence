# Analytics API Contract

## Overview
This document defines the API contract for the Read-Only Civic Analytics service. The API exposes deterministic, mathematically rigorous computations from the `CivicAnalyticsEngine`.

## Current State (Phase 6.2)
- **Data Source**: Currently abstracts over `data/normalized/normalized_villages.csv` (local repository pattern).
- **BigQuery Path**: The API is structurally decoupled via `AnalyticsRepository` to seamlessly integrate BigQuery querying in production without changing the API payload.
- **Citizen Demand**: Currently missing. All responses gracefully default to the `PUBLIC_EVIDENCE_ONLY` readiness state.

## Endpoints

### 1. Analytics Summary (`GET /api/analytics/summary`)
Returns aggregated deterministic gap analysis across the complete mapped dataset.

**Response Schema (`AnalyticsSummary`)**
```json
{
  "total_villages_analyzed": "Integer (e.g. 16002)",
  "total_households": "Integer",
  "total_fhtc": "Integer",
  "total_reported_household_gap": "Integer",
  "readiness_state": "String (PUBLIC_EVIDENCE_ONLY)",
  "calculation_version": "String (v1.0)",
  "data_source": "String"
}
```

### 2. Village Lookup (`GET /api/analytics/village/{lgd_village_code}`)
Returns detailed analytical factors and readiness state for a single canonical village.
Returns `404 Not Found` if the code does not exist.

**Response Schema (`PriorityResult`)**
```json
{
  "lgd_village_code": "String",
  "readiness": "String (PUBLIC_EVIDENCE_ONLY)",
  "evidence_quality": "String",
  "calculation_version": "String",
  "normalized_gap": "Float [0.0, 1.0]",
  "normalized_exposure": "Float [0.0, 1.0]",
  "normalized_demand": "Float [0.0, 1.0]",
  "reported_household_gap": "Integer",
  "household_exposure": "Integer",
  "priority_score": "Float | Null"
}
```

## Security & Architectural Boundaries
- Endpoints are explicitly READ-ONLY.
- No direct SQL execution via query parameters.
- Priority engine normalization bounds and saturation limits strictly enforced on outputs.
