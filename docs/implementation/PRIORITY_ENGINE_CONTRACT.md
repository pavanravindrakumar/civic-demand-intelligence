# Priority Engine Contract

## 1. Overview
The Priority Engine creates deterministic ordering signals (`PriorityAssessment`) from verified `ConvergenceOpportunity` records. It operates purely analytically and never leverages GenAI, LLMs, or probabilistic reasoning to calculate scores.

Crucially, **it produces priority scores, NOT policy decisions.** It does not allocate funds, predict project success, or establish political "winners".

## 2. Eligibility & Strict Bounding
- A score is ONLY computed when the opportunity reaches `CONVERGENCE_IDENTIFIED` (where verified citizen demand properly converges with an explicit public infrastructure gap).
- `PUBLIC_EVIDENCE_ONLY`, `DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE`, and `INCOMPLETE_CONVERGENCE` states are intentionally excluded from generating a combined priority score.

## 3. Configured Factor Weights
Priority scores are derived from a versioned configuration (`PriorityWeights`). Magic numbers in the code are prohibited. Changing the weights requires bumping the configuration version.

## 4. Normalization and Bounding
Each factor contribution is bounded between `[0.0, 1.0]` before weights are applied:
- **Gap Normalization**: `(reported_household_gap / household_exposure)` bounded to `1.0`. Prevents absurd mathematical edge cases.
- **Exposure Normalization**: `(household_exposure / MAX_HOUSEHOLDS_CAP)` bounded to `1.0`. Operates as an exposure proxy, NOT a demographic population count.
- **Demand Normalization**: `(signal_count / MAX_DEMAND_CAP)` bounded to `1.0`. Explicitly saturates at a ceiling to prevent deliberate manipulation via signal flooding.

## 5. Evidence Semantics
- **No arithmetic mixing**: `signal_count` is NEVER subtracted from `reported_household_gap`.
- **No population assumptions**: The engine does NOT guess or estimate the final number of beneficiaries.

## 6. Auditability
The output strictly exposes:
- The final score.
- The precise `factor_contributions` and `factor_inputs_normalized`.
- A link to the upstream `opportunity_id` for exact provenance tracing to the raw Citizen Signals and JJM data.
