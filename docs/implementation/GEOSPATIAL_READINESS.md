# Geospatial Data Readiness Report

## Executive Summary
This audit evaluated the current Civic Demand Intelligence architecture, specifically examining the normalized dataset (`normalized_villages`), the BigQuery schema (`schema_v1.sql`), and the frontend dependencies to determine if the existing stack can support a policymaker map/hotspot visualization.

**Conclusion:** The current dataset is **NOT** geospatially ready. It lacks the coordinate or geometry data required to plot points or boundaries on a map. LGD codes alone are insufficient for rendering without an accompanying geospatial reference dataset.

## A. Current Available Geographic Fields
The current dataset (`data/normalized/normalized_villages.csv` and BigQuery schema) contains exclusively nominal/hierarchical geographic identifiers:
* `state`
* `district`
* `block`
* `panchayat`
* `village_name` (LGD or JJM fallback)
* `lgd_village_code` (Canonical ID)
* `jjm_village_id`

## B. Fields That Are Missing
To support any map visualization, the dataset strictly requires, but is entirely missing:
* Latitude (`lat`)
* Longitude (`lng` / `lon`)
* Geometric boundaries (e.g., `WKT`, `GeoJSON`, `geometry` column)
* Geographic centroids

## C. Can the Current Data Directly Support a Real Village-Level Map?
**No.** Map libraries (like Mapbox, Leaflet, or Google Maps) require spatial coordinates (latitude/longitude) or geometries to render elements on a map. The `lgd_village_code` is a governmental administrative ID, not a spatial coordinate. Geocoding based solely on village names is notoriously unreliable and leads to severe inaccuracies due to duplicate names across different districts or states.

## D. Minimum Additional Geographic Source Required
To build an evidence-backed map, the architecture requires a **Geospatial Reference Dataset (Lookup Table)** that maps `lgd_village_code` to at least a geographic centroid (latitude/longitude) for point rendering, or a boundary polygon for choropleth mapping.

## E. Recommended Source Strategy
The source should ideally be:
1. **Official Government Geography:** A verified shapefile/GeoJSON from an authoritative source (e.g., Survey of India, LGD spatial datasets, or localized government GIS portals) that explicitly keys geometries to LGD codes.
2. **Clearly Labelled Synthetic Demo Data (If Official is Unavailable):** If an official LGD-to-coordinate dataset cannot be procured for this hackathon phase, the system MUST use a explicitly generated synthetic spatial lookup table (e.g., random points bounding within the correct district) and *clearly label the UI* to indicate that the locations are synthetic/proxy representations of real data, upholding the "no fabricated evidence without disclosure" policy.

## F. Implications for the Architecture
* **Village Markers:** Cannot be plotted until lat/long coordinates are obtained.
* **Hotspot Visualization:** Spatial clustering (e.g., heatmap) is impossible without coordinates.
* **District/Block Aggregation:** We can currently perform *tabular* aggregation (GROUP BY district) in BigQuery, but we cannot render choropleth maps of districts without district-level boundary geometries.
* **BigQuery GIS:** BigQuery's `ST_GEOGPOINT` and spatial indexing cannot be utilized until coordinate data is imported.
* **Frontend Rendering:** An inspection of `frontend/package.json` confirms that **no map library (e.g., `mapbox-gl`, `react-map-gl`, `leaflet`) is currently installed**.

## G. Recommended Next Implementation Boundary
**Phase 7.2D.2: Acquire and Integrate Geospatial Reference Data.**
Before touching the frontend UI, the backend data pipeline must be updated to ingest a geospatial reference file (mapping `lgd_village_code` to `lat`, `lng`), join it to the normalized dataset, and update the BigQuery schema to support GIS features. Only after the backend serves coordinates should frontend map components be introduced.
