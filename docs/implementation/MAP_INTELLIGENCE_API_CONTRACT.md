# Map Intelligence API Contract

## 1. Overview
The Map Intelligence API provides the browser-facing data layer for the frontend civic-demand map. It resolves the N+1 problem by performing a server-side indexed deterministic join between immutable geographic boundaries and dynamic analytics.

## 2. Endpoint Configuration
* **Route:** `GET /api/geo/hotspots`
* **Purpose:** Returns a bounded GeoJSON `FeatureCollection` sorted strictly by hotspot intensity for map rendering.

## 3. Supported Filters
* `district` (string, optional): Restricts results to villages within the specified district.
* `block` (string, optional): Restricts results to villages within the specified block.
* `limit` (integer, default 100, max 1000): Enforces a hard server-side payload cap to prevent browser out-of-memory errors.

## 4. Hotspot Metric Semantics
* **Primary Metric:** `reported_household_gap`
* **Definition:** The absolute number of households without functional household tap connections (FHTC) as reported in the JJM public dataset.
* **Ordering Rules:** Results are deterministically sorted by `reported_household_gap` (Descending), followed by `lgd_village_code` (Ascending) as a stable tie-breaker.
* **Important Priority Rule:** The map visualizes the *Reported Household Tap-Connection Gap*. If `validated_citizen_demand_count` is absent (as it is in the current public dataset), `priority_score` remains `null`. The backend **does not** fabricate priority rankings based solely on the gap.

## 5. Response Schema
Returns standard GeoJSON where each `Feature` contains a `properties` dictionary heavily tailored to the browser map:

```json
{
  "type": "Feature",
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "properties": {
    "lgd_village_code": "586842",
    "village_name": "Addateegala",
    "district": "Alluri Sitharama Raju",
    "block": "ADDATEEGALA",
    "panchayat": "ADDATEEGALA",
    "reported_household_gap": 379,
    "household_exposure": 1515,
    "evidence_quality": "PARTIAL",
    "readiness": "PUBLIC_EVIDENCE_ONLY",
    "priority_score": null
  }
}
```

## 6. Join Mechanism & Geometry Coverage
* **Join Key:** The deterministic `lgd_village_code`.
* **Coverage Constraints:** 15,925 out of 16,002 villages have corresponding coordinates. The 77 unmatched villages are intentionally excluded from this geographic response (and do not receive synthetic coordinates).
* **Performance Rationale:** The geo repository loads the simplified WGS84 GeoJSON into memory at startup. The analytics repository loads the csv cache into a hash map at startup. The `/api/geo/hotspots` endpoint simply cross-references these in-memory data structures (O(1) lookup), achieving sub-millisecond join times without needing Redis or a SQL spatial extension.
