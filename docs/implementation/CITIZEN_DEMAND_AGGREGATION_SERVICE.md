# Citizen Demand Aggregation Service

## 1. Overview
The `CitizenDemandAggregator` provides the deterministic transformation from raw individual `CivicNeed` entities into grouped `CitizenDemandEvidence`. It is a pure data-pipeline operation and does not invoke AI.

## 2. Service Interface
**Input:** A list of `CivicNeed` records and a bounded time window (`window_start`, `window_end`).
**Output:** A list of `CitizenDemandEvidence`.

## 3. Rebuild Semantics
Demand Aggregation is treated as a **derived, rebuildable artifact**.
- It does not attempt complex stateful merges or updates.
- Running the aggregator for a timeframe completely replaces the previous output artifact via `CitizenDemandEvidenceRepository.overwrite_evidence()`.
- This ensures absolute idempotency. Data errors or upstream extraction bugs can be fixed by simply wiping the evidence artifact and rerunning the aggregator over the immutable signal/need source data.

## 4. Deduplication
The aggregator utilizes a standard Python set constraint to deduplicate exactly by `source_signal_id` for any given need-category/village combination. If upstream intake idempotency fails, the aggregator acts as the ultimate circuit breaker ensuring one submission equals one signal count.

## 5. Local Repository
Persistence leverages a local `JSONL` file at `data/local_development/citizen_demand_evidence.jsonl`. No remote distributed databases are necessary for this MVP boundary.

## 6. Testing Strategy
- Tests are entirely offline, leveraging dependency injection.
- Scenarios include deduplication logic, unresolved geography preservation, multi-need independence (different aggregates), distinct submitter logic, and out-of-bounds time window exclusions.
- Complete execution of the aggregator makes **zero** live API calls and invokes **no** BigQuery mutations.
