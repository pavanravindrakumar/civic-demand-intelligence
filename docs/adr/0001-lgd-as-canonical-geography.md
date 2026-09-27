# ADR-001: LGD as Canonical Geographic Identity

**Status:** Accepted
**Date:** 2026-09-24

---

## Context

The platform must join citizen signals, government evidence, and administrative geography from disparate sources that each use their own location identifiers.

Sources have incompatible geographic IDs:
- JJM uses village names (string-based)
- Mission Antyodaya uses Gram Panchayat codes
- Census 2011 uses Census Location Codes
- APSAC uses internal GIS IDs
- Citizens use natural-language place names

Without a canonical identity layer, cross-source joins are unreliable, especially given the 2022 Andhra Pradesh district reorganization that changed 13 districts to 26.

## Decision Drivers

- Must support cross-source joins without GIS geometry
- Must handle historical data mismatches (pre/post AP 2022)
- Must be nationally authoritative (not state-specific)
- Must be tabular (numeric codes), not spatial

## Considered Options

### Option 1: LGD Numeric Codes (chosen)
The Ministry of Panchayati Raj Local Government Directory assigns unique numeric codes to every administrative entity from State to Village.
- Pros: National authority, immutable numeric codes, bulk CSV download, hierarchy preserved, versioned with major/minor release
- Cons: NAPIX live API has auth complexity (mitigated by static CSV)

### Option 2: Census Location Codes
2011 Census codes used in demographic data
- Pros: Good for Census-linked data
- Cons: Outdated (2011); no update since; 2026 reorganizations not reflected

### Option 3: String-based District Names
Use district names as join keys
- Pros: Simple to implement
- Cons: Catastrophic for AP 2022 reorganization; name variations across sources; not machine-reliable

### Option 4: Spatial Geometry (PostGIS/ST_Intersects)
Use boundary polygons for spatial joins
- Pros: True geographic containment logic
- Cons: Requires GIS infrastructure; APSAC WMS is image tiles (no WFS); infeasible in 6-day timeline

## Decision

Use LGD numeric codes as the universal foreign key across all tables.

- Source-native IDs are preserved in dedicated columns alongside the LGD code
- A `lgd_historical_mapping` table bridges pre-2022 to post-2022 AP district codes
- Resolution from source name to LGD code uses fuzzy string matching with confidence tracking
- `resolution_status` (CONFIRMED / PROBABLE / UNRESOLVED) is always explicit

## Consequences

### Positive
- All cross-source joins are numeric and reliable
- AP 2022 reorganization is handled by one reconciliation table, not complex GIS
- Source-native IDs preserved for auditability
- Confidence/status exposed for all resolutions

### Negative
- Initial fuzzy matching requires tuning for Indian name variations
- AP historical mapping table must be manually validated on Day 1
- Unresolved geographies cannot have gap calculations (acceptable -- they are exposed)

### Risks
- JJM village names may have significant spelling variations
- Mitigation: Levenshtein distance + manual review queue for PROBABLE matches
