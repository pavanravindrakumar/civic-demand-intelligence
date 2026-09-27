# Priority Snapshot Contract

## Purpose
This document defines the contract for future BigQuery snapshot tables that will materialize deterministic civic demand intelligence. **These tables do not exist yet.** The civic analytics priority engine is designed to operate on these structured outputs to ensure reproducible intelligence.

## Architectural Constraints
- **NO LLM MATH**: Priority scores and ranks are calculated deterministically by the analytics engine. LLMs only interpret and explain these scores.
- **NO LIVE MATERIALIZED VIEWS FOR CORE INTELLIGENCE**: Priority snapshots are explicitly versioned, precomputed tables to guarantee reproducibility and auditability.

## Future Snapshot Schema
A precomputed priority snapshot table MUST contain at least the following fields:

- `snapshot_id` (STRING): Unique identifier for the run.
- `snapshot_timestamp` (TIMESTAMP): Execution timestamp.
- `geography_version` (STRING): The version of the LGD / boundary map used.
- `source_version` (STRING): References to the exact JJM / other source data version.
- `calculation_version` (STRING): Version of the `CivicAnalyticsEngine` logic (e.g., `v1.0`).
- `lgd_village_code` (STRING): Canonical identifier for joining to maps.
- `sector` (STRING): e.g., "Water".
- `indicator` (STRING): e.g., "reported_household_tap_connection_gap".
- `convergence_state` (STRING): The state of evidence convergence (e.g., `CONVERGENCE_IDENTIFIED`, `PUBLIC_EVIDENCE_ONLY`).
- `factor_normalized_gap` (FLOAT): [0.0 - 1.0] Bounded severity of the infrastructure gap.
- `factor_normalized_exposure` (FLOAT): [0.0 - 1.0] Bounded footprint / households impacted.
- `factor_normalized_demand` (FLOAT): [0.0 - 1.0] Bounded, deduplicated citizen demand volume.
- `priority_score` (FLOAT): [0.0 - 1.0] Deterministic final score. **Null if convergence_state is not CONVERGENCE_IDENTIFIED.**

## Current Architecture Integration
The snapshot schema conceptually aligns with the newly structured deterministic pipeline:
`Citizen Signal → Civic Need → Citizen Demand Evidence + Public Evidence → Unmet Demand Assessment → Convergence Opportunity → Priority Assessment`

With the new pipeline architecture, snapshots will trace back directly to the exact `opportunity_id` and the `factor_contributions` map exposed by the `ConvergencePriorityEngine`.

The engine continues to support `PUBLIC_EVIDENCE_ONLY` baselines correctly without inventing phantom priority scores.
