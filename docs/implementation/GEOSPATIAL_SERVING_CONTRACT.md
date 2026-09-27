# Geospatial Serving Contract

## 1. Overview
The geospatial serving layer bridges the gap between the heavy, unprojected raw village boundaries and the fast, WGS84-based requirements of modern web mapping libraries (like Mapbox, MapLibre, Leaflet). It exposes a read-only FastAPI endpoint that serves optimized map geometry, enabling the frontend to render villages without bogging down the browser.

## 2. Artifacts
* **Raw Artifact:** `data/raw/geospatial/vb_soi_ap_geojson.zip` (114 MB uncompressed, `EPSG:7755`, full census columns)
* **Normalized Artifact:** `data/normalized/village_geometry.geojson` (43 MB, `EPSG:7755`, only LGD matched features, stripped properties)
* **Browser Map Artifact:** `data/normalized/village_map.geojson` (10.75 MB, `EPSG:4326` WGS84, simplified geometry, UI properties)

## 3. Reprojection & Simplification Policy
* **Reprojection:** Features are strictly reprojected from `EPSG:7755` (Kalyanpur 1975) to `EPSG:4326` (WGS84) using `pyproj`. This ensures compatibility with web mapping tools which expect WGS84 coordinates.
* **Simplification:** Due to the large size of the highly detailed normalized artifact (43 MB), the polygons are simplified using the Douglas-Peucker algorithm (via Shapely's `simplify`) with a tolerance of `0.001` degrees (~111 meters). `preserve_topology=True` is utilized to prevent polygon gaps. This shrinks the payload to 10.75 MB, a 75% reduction, making it highly suitable for rapid browser loading.

## 4. Unmatched Villages (Coverage Limitation)
* The join between the raw geospatial data and our unified JJM/LGD data covered 15,925 out of 16,002 villages (99.52%).
* The remaining 77 villages intentionally have no coordinates generated or inferred. The API and frontend gracefully support missing geometry (representing them in tables/dashboards only).

## 5. API Contract
* **Route:** `GET /api/geo/villages`
* **Response Format:** standard `GeoJSON FeatureCollection`
* **Supported Filters:**
  * `district` (string, optional)
  * `block` (string, optional)
  * `limit` (integer, default 1000, max 10000)
* **Single Fetch Route:** `GET /api/geo/villages/{lgd_village_code}` returns a single GeoJSON `Feature` or a `404`.

## 6. Response Fields (Properties)
The geometry properties are purposely narrow to minimize wire payload:
* `lgd_village_code`
* `village_name`
* `district`
* `block`
* `panchayat`

## 7. Browser-Facing Map Intelligence (The Join Layer)
While `GET /api/geo/villages` serves raw boundaries, the primary endpoint for frontend visualization is the Map Intelligence API.
* It natively joins geometry with civic demand analytics (e.g. `reported_household_gap`) server-side using `lgd_village_code`.
* It applies strict deterministic ranking to return bounds-safe hotspot vectors.

For the full contract outlining metric mapping, limits, and the deterministic join, please refer to:
[MAP_INTELLIGENCE_API_CONTRACT.md](MAP_INTELLIGENCE_API_CONTRACT.md)
