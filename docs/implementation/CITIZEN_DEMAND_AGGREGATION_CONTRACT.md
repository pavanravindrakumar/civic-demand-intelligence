# Citizen Demand Aggregation Contract

## 1. Overview
This contract governs the deterministic grouping and deduplication of individual `CivicNeed` records into `CitizenDemandEvidence`. It represents the bridge between highly granular citizen submissions (signals) and generalized population demand.

## 2. Evidence Model
The canonical aggregate is `CitizenDemandEvidence`. It explicitly summarizes demand without inventing prioritization or demographic statistics.
- **demand_id**: Unique UUID for the aggregate.
- **aggregation_window_start / end**: Bounding time constraints for the demand calculation.
- **signal_count**: Count of unique `source_signal_id` values. This strictly represents the volume of signals, NOT the number of human beneficiaries or households.
- **distinct_submitter_count**: Count of unique `submitter_pseudonym` values where available. Provides a floor on human diversity.
- **source_channels**: The distinct list of channels (e.g., `["TEXT", "VOICE"]`) that contributed to the aggregate.

## 3. Grouping Strategy
Aggregates are grouped strictly by:
1. `canonical_need_type`
2. `lgd_village_code`

If multiple `CivicNeed` types are identified in a single village (e.g., `WATER_SUPPLY_DEFICIT` and `ROAD_CONNECTIVITY_DEFICIT`), they remain distinct aggregates. They are not collapsed into a generic "complaint bucket" at this layer.

## 4. Geography Handling
Signals without an `lgd_village_code` (unresolved geography) are aggregated with `lgd_village_code = None`. They are inherently excluded from village-level analytics but are retained as unresolved systemic demand.

**Prohibited Geographic Operations:**
- No fuzzy matching village names to force resolution.
- No geocoding or spatial inferences from text.

## 5. Deduplication
- Multiple interpretations of the same `source_signal_id` (e.g., in a race condition upstream) are collapsed deterministically during aggregation. They count as exactly 1 towards `signal_count`.

## 6. Prohibited Statistics
At this layer, the system does **not** calculate:
- Priority scores
- Unmet demand
- Required funding
- Population or household gaps

It purely presents the volume and diversity of citizen demand evidence.
