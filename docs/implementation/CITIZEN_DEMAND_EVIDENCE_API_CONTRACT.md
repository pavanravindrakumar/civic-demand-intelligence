# Citizen Demand Evidence API Contract

## 1. Overview
The Citizen Demand Evidence API exposes read-only aggregated citizen demand data. It strictly acts as a data boundary: it delivers evidence counts and bounds without inferring demographic statistics, projecting budgets, or calculating final civic prioritization.

## 2. Endpoints

### `GET /api/demand/evidence`
Retrieves a global list of demand aggregates, subject to filtering and server-side limits.

**Query Parameters:**
- `canonical_need_type`: Filter by a specific structured need (e.g. `WATER_SUPPLY_DEFICIT`).
- `sector`: Filter by sector mapping (e.g. `WATER`).
- `lgd_village_code`: Restrict to a specific exact 6-digit village code.
- `geography_status`: Options are `RESOLVED` (only aggregates mapped to a village) or `UNRESOLVED` (only unmapped aggregates).
- `window_start` / `window_end`: Filter for aggregates bounded within this time range.
- `limit`: Default `100`, max `1000`.

**Ordering (Deterministic):**
Returns data sorted by:
1. `signal_count` (Descending - highest volume first)
2. `lgd_village_code` (Ascending)
3. `canonical_need_type` (Ascending)

---

### `GET /api/demand/evidence/{lgd_village_code}`
Retrieves all explicitly resolved demand aggregates belonging to a single 6-digit village code.

**Query Parameters:**
- `window_start` / `window_end`: Filter aggregates bounded within this time range.

**Ordering (Deterministic):**
Returns data sorted by:
1. `signal_count` (Descending)
2. `canonical_need_type` (Ascending)

**Semantics:**
Different `canonical_need_type` clusters remain separate objects. They are *not* squashed into a generic "village demand score". Unresolved geography aggregates are mathematically excluded from this route.

## 3. Response Schema (`CitizenDemandEvidenceResponse`)
```json
{
  "demand_id": "uuid",
  "canonical_need_type": "WATER_SUPPLY_DEFICIT",
  "sector": "WATER",
  "lgd_village_code": "111111",
  "aggregation_window_start": "2023-01-01T00:00:00Z",
  "aggregation_window_end": "2023-01-31T23:59:59Z",
  "signal_count": 50,
  "distinct_submitter_count": 45,
  "source_channels": ["TEXT", "VOICE"],
  "latest_signal_at": "2023-01-30T10:00:00Z",
  "aggregation_version": "demand-v1"
}
```

## 4. Count Semantics & Privacy Boundary
- **`signal_count`**: The exact number of individual, deduplicated Citizen Signals interpreted for this category. **DO NOT** present this to users as "number of citizens affected" or "population".
- **`distinct_submitter_count`**: The number of unique pseudonym footprints. This provides an approximate floor of distinct actors but still **cannot** be legally or statistically treated as a verified population count.
- **Privacy**: The API intentionally excludes `contributing_signal_ids` from the output response. It does not return raw text, nor does it return any individual citizen identities or PII.

## 5. Explicit Exclusions
This API explicitly **does not** compute or serve:
- Priority Scores
- Unmet Demand Calculations
- Estimated Project Funding / Costing
- AI "Thoughts" or reasoning traces.
