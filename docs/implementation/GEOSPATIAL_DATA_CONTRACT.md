# Geospatial Data Contract

## 1. Identifiers
* **Source Geometry Identifier:** The `vlcode` field in the raw NWDP GeoJSON must be used as the unique spatial key.
* **Canonical Application Identifier:** The `lgd_village_code` field is the universal key for all civic data in this application.
* **Join Rules:** The join must be a strict 1:1 deterministic mapping (`vlcode` == `lgd_village_code`). Fuzzy matching on village names or spatial inference is strictly prohibited.

## 2. Geometry & CRS
* **Geometry Field:** The `geometry` object of the GeoJSON feature contains the polygon/multipolygon boundaries for the village.
* **Coordinate Reference System (CRS):**
  - The raw source dataset is provided in `EPSG:7755` (Kalyanpur 1975).
  - Any normalized output artifacts serving the web frontend MUST project this geometry to `EPSG:4326` (WGS84) to be valid for browser mapping libraries (Mapbox, Leaflet, Google Maps).
* **Invalid Geometry Handling:** Any feature lacking a valid `geometry` object (or missing `coordinates`) must be discarded. They must not be filled with synthetic or inferred points.

## 3. Provenance & Attribution
* **Provenance Requirements:** The raw zip archive must be stored immutably in `data/raw/geospatial/`. It must never be overwritten.
* **Source Attribution:** The dataset originates from the Geological Survey of India / National Water Informatics Centre. All UI map components rendering this data must prominently carry the attribution: "Map Boundaries © Geological Survey of India / NWIC".

## 4. Coverage Expectations
* **Target Coverage:** At least 99% of `normalized_villages` must map to a geometry.
* Villages that fail to join will gracefully degrade in the UI by falling back to tabular data only. No "default coordinates" will be generated for unmatched villages.

## 5. Storage Rules
* **Raw Storage:** `data/raw/geospatial/vb_soi_ap_geojson.zip`
* **Normalized Storage:** `data/normalized/village_geometry.geojson`. The normalized artifact must strip all extraneous property columns from the raw file (e.g. population metrics from the 2011 census that are out of date) and retain only `lgd_village_code`, `village_name`, and `source_attribution`.
