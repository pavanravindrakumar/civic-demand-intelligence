# Policymaker Hotspot Map

## 1. Overview
The policymaker hotspot map visualizes village-level civic water demand infrastructure gaps across Andhra Pradesh. It serves as a visual prioritization tool based firmly on deterministic metrics, designed specifically for decision-makers.

## 2. Technical Stack
* **Mapping Library:** React-Leaflet (`react-leaflet` and `leaflet`)
* **Rationale:** Leaflet is an open-source, lightweight map engine that requires zero configuration tokens (unlike Mapbox), incurs no cloud billing for vector rendering, and works perfectly for polygon-based GeoJSON overlay maps. It satisfies the strict project boundary against adding new cloud dependencies or exposing secrets.
* **Server-Side Rendering (SSR):** Next.js cannot render Leaflet maps server-side because Leaflet relies on the browser's `window` object. A Next.js dynamic import with `ssr: false` (`HotspotMapClient` via `HotspotMap.tsx`) handles this boundary gracefully.

## 3. Data Integration & Performance
* **Data Source:** Fetches exclusively from the bounded endpoint `GET /api/geo/hotspots`.
* **Payload Constraints:** Limits map responses to 1,000 features max. The map avoids loading the raw 10.75 MB dataset, guaranteeing that the browser does not crash.
* **Filter State:** District, block, and top-N limits are available. Changes to filters trigger a fresh fetch to the bounded backend API to get the correct deterministic slice of data, avoiding N+1 requests and client-side sorting.
* **Initialization:** A `FitBounds` component ensures that the viewport automatically snaps to the loaded feature bounds (statewide or district-wide depending on the data).

## 4. Semantic Rules
* **Map Metric:** Visual intensity (chloropleth styling) is strictly mapped to `reported_household_gap`.
* **Priority Suppression:** `priority_score` remains correctly unvisualized because the public data artifact guarantees no valid citizen demand requests currently exist, enforcing the `PUBLIC_EVIDENCE_ONLY` boundary.
* **Colors:** Uses a sequential heat scale (Yellow to Dark Red) based on gap thresholds.
* **Labeling:** Explicitly labeled "Reported Household Tap-Connection Gap". The terms "Population" (for exposure) and "Citizen Demand" are avoided in the map UI.

## 5. Coverage Honesty
* **Missing Geometry:** 77 analytic villages do not have paired NWDP boundary geometry. The map explicitly states this in its legend footer. Fallback coordinates are intentionally not generated, preserving data integrity.

## 6. Testing Strategy
* Leaflet interacts heavily with WebGL/DOM elements, making standard headless React testing difficult.
* `HotspotMapClient` abstracts the network calls through `api.ts`.
* Tests mock Leaflet components to assert React logic: loading states, error states, API limits, and successful feature-count rendering without crashing Vitest. All 17 frontend tests pass.
