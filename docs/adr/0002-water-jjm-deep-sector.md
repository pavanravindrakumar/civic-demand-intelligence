# ADR-002: Water/JJM as MVP Deep Sector

**Status:** Accepted
**Date:** 2026-09-24

---

## Context

The MVP must demonstrate one complete intelligence chain from citizen signal to Intelligence Report. The depth of this chain depends entirely on the quality and computability of the evidence for the chosen sector.

The challenge requires a development sector where:
- Gap can be calculated deterministically (no LLM arithmetic)
- Data is nationally available and granular
- Gap logic is understandable to non-technical judges and policymakers
- Data can be safely loaded as a static snapshot within the hackathon timeline

## Considered Sectors

### Option 1: Water / Jal Jeevan Mission (chosen)

Gap logic: `unmet_households = total_households - fhtc_households`

| Criterion | Assessment |
|-----------|-----------|
| Gap measurability | EXCELLENT -- simple arithmetic |
| Data granularity | Village-level |
| Data availability | National dashboard; state PDFs; CSV extract |
| Data recency | 2025/2026 updates |
| 6-day feasibility | HIGH |
| Joins to LGD | Name normalization only |
| LLM involvement in gap | None required |
| Demo clarity | "N households have no tap water" -- universally understood |

### Option 2: Roads / PMGSY

Gap logic: sanctioned_km - completed_km (but this doesn't identify which habitation)

| Criterion | Assessment |
|-----------|-----------|
| Gap measurability | POOR -- length deficit doesn't identify impacted population |
| Data granularity | District/block level (not village) |
| Spatial routing required | YES -- to determine actual access deficit |
| 6-day feasibility | LOW |
| LLM involvement | Required for interpretation -- not acceptable |

### Option 3: Sanitation / SBM-G

Gap logic: ODF villages vs non-ODF

| Criterion | Assessment |
|-----------|-----------|
| Gap measurability | MODERATE -- binary (ODF/non-ODF) |
| Data recency | Mainly 2019-2020 era |
| Data availability | Lower fidelity than JJM |
| 6-day feasibility | MEDIUM |

### Option 4: Health / HFM

Gap logic: habitations outside X km of health facility

| Criterion | Assessment |
|-----------|-----------|
| Gap measurability | POOR without spatial analysis |
| Spatial required | YES |
| 6-day feasibility | LOW |

## Decision

**Water and Sanitation -- Jal Jeevan Mission (JJM)** is the MVP deep sector.

JJM is the only sector where:
1. The gap is a single arithmetic operation
2. The gap value is directly meaningful to policymakers ("41,230 households without water")
3. Village-level data is available nationally
4. No spatial analysis is required

All other sectors either require spatial routing or produce less interpretable gap metrics.

## Consequences

### Positive
- Gap calculation requires zero LLM involvement
- Data can be fully loaded as static snapshots
- Gap value is universally understandable
- JJM data covers the AP pilot geography well

### Negative
- Platform appears water-focused at demo time
- Judges may ask about extensibility to other sectors

### Mitigations
- Sector adapter pattern documented and shown in architecture
- `sector` field in all schemas -- adding a new sector means a new adapter, not redesign
- Roads as "future adapter" is explicitly mentioned in demo narrative

### Post-MVP Path
Roads (PMGSY) can be added as a sector adapter once:
- Village-level road data is available
- A non-spatial gap proxy is identified (e.g., unconnected habitations count)

---

# ADR-003: BigQuery as Analytical Backbone

**Status:** Accepted
**Date:** 2026-09-24

---

## Context

The platform needs an analytical database that can:
- Handle large tables (full India LGD = ~600,000 villages)
- Run complex SQL aggregations for hotspot calculations
- Support partitioned queries by date for snapshot management
- Require zero operational overhead during the 6-day sprint

## Considered Options

### Option 1: BigQuery (chosen)
- Pros: Serverless, managed, scales to petabytes, partitioned tables, no ops, Cloud Run connects directly, free sandbox tier
- Cons: Query latency (seconds, not milliseconds) -- acceptable for dashboard use case; no row-level transactions (not needed)

### Option 2: Cloud SQL (PostgreSQL)
- Pros: ACID transactions, familiar SQL, low latency
- Cons: Requires VPC setup, Connection Pooling configuration, ongoing maintenance, instance cost, slower to set up in 6-day sprint

### Option 3: Firestore
- Pros: Real-time; Firebase integration
- Cons: Not relational; aggregation queries very awkward; cannot do JOIN-based intelligence calculations

### Option 4: SQLite (local)
- Pros: Zero setup
- Cons: Cannot run in Cloud Run at scale; not acceptable for a production-oriented platform

## Decision

BigQuery is the analytical backbone for all canonical, derived, and intelligence data.

The Civic Need graph (links between needs) is represented as a relational JOIN table (`need_links`) within BigQuery. No graph database is needed -- the links are simple many-to-many relationships.

## Consequences

### Positive
- Zero operational overhead
- Scales to full India LGD with no architecture change
- Complex aggregations (hotspot calculations) run natively in SQL
- Easy integration with Python data science tools post-MVP

### Negative
- Query latency (1-5 seconds for complex aggregations) -- mitigated by response caching
- No sub-second response times -- dashboard must show loading states

### Risks
- BigQuery slot contention under concurrent load
- Mitigation: For demo, pre-compute hotspot aggregations and cache results
