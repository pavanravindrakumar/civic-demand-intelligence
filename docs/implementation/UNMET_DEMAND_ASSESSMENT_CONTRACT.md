# Unmet Demand Assessment Contract

## 1. Overview
The Unmet Demand Assessment mathematically represents the *convergence* of public infrastructure evidence with citizen demand evidence. It creates a deterministic mapping between what citizens are reporting (demand) and what public datasets claim (infrastructure gaps).

Crucially, **Unmet Demand is an evidence state, not an arbitrary calculation.**

## 2. Prohibited Calculations
- **No arithmetic subtractions between domains**: We do NOT subtract `signal_count` from `reported_household_gap`. These measure fundamentally different units.
- **No population inference**: `signal_count` is the volume of interpreted signals, not the count of people affected.
- **No Priority Assignment**: This assessment prepares evidence. It deliberately avoids creating a `priority_score` or ranking villages.

## 3. Assessment Model
The canonical output is the `UnmetDemandAssessment` model.
Fields include:
- `evidence_state`: The core qualitative outcome of the join (see below).
- `canonical_need_type`: The explicit structured civic need being evaluated.
- `public_evidence_vintage` & `reported_household_gap`: Preserved explicitly from the public source.
- `demand_aggregation_window_start`/`end` & `signal_count`: Preserved explicitly from the citizen demand source.

## 4. Join and Alignment Strategy
- **Geographic Join**: Exact match on `lgd_village_code`. Unresolved citizen demand is deliberately left unmapped; the system does not infer or fuzzy-match geography.
- **Semantic Need Alignment**: The core mapping relies on `canonical_need_type`. Currently, public JJM evidence only provides data for `WATER_SUPPLY_DEFICIT`. Other civic needs (roads, education, health) do NOT inherit JJM's public infrastructure status.

## 5. Assessment States (`evidence_state`)
The engine categorizes the evidence convergence into strictly typed deterministic states:
- `DEMAND_SUPPORTED`: Citizen demand exists, and relevant public infrastructure gap data is available for that exact need type.
- `PUBLIC_EVIDENCE_ONLY`: Public evidence exists, but there is zero citizen demand recorded. This explicitly defines a public baseline, refusing to hallucinate citizen demand.
- `DEMAND_WITHOUT_MATCHING_PUBLIC_EVIDENCE`: Citizen demand exists for a need type (like `WATER_SUPPLY_DEFICIT`) but the village lacks a public infrastructure record.
- `NO_RELEVANT_PUBLIC_EVIDENCE`: Citizen demand exists for a need type (like `ROAD_CONNECTIVITY_DEFICIT`) which the public data system currently does not track or support.

## 6. Provenance and Rebuildability
Assessments are derived, rebuildable artifacts. They preserve temporal alignments explicitly by tracking both the public dataset vintage and the citizen demand aggregation window alongside the calculation version.
