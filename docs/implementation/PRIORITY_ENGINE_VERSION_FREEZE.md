# Priority Engine Version Freeze

**1. Active Version:**
1.0.0-final

**2. Final/Draft Status:**
FINAL. The implementation exactly matches the contract, bounds are explicit, and factors are mathematically reproducible.

**3. Active Factors:**
Only exactly 3 factors are implemented:
- Infrastructure Gap (`normalized_gap`)
- Exposure Proxy (`normalized_exposure`)
- Validated Citizen Demand (`normalized_demand`)

**4. Weights:**
- `infrastructure_gap`: 0.5
- `household_exposure`: 0.2
- `validated_demand`: 0.3

**5. Normalization Methods:**
- **Gap**: `reported_household_gap / household_exposure` (bounded to max `1.0`, `0.0` if denominator is 0).
- **Exposure Proxy**: `household_exposure / MAX_HOUSEHOLDS_CAP` (MAX_HOUSEHOLDS_CAP = 1000.0, bounded to max `1.0`).
- **Validated Demand**: `signal_count / MAX_DEMAND_CAP` (MAX_DEMAND_CAP = 50.0, bounded to max `1.0`).

**6. Missing-Input Rules:**
- Missing `reported_household_gap` or `household_exposure` defaults to `0`.
- Missing `signal_count` defaults to `0`.
- Division by zero is avoided (yields `0.0` normalization).

**7. Eligibility Rules:**
- Scoring is ONLY executed when `ConvergenceOpportunity.convergence_state` is EXACTLY `CONVERGENCE_IDENTIFIED`.
- `PUBLIC_EVIDENCE_ONLY`, `DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE`, `INCOMPLETE_CONVERGENCE` states result in NO PRIORITY SCORE (i.e. not assessed or score=null equivalent).
- Unresolved geography or unsupported public-evidence pairing cannot produce `CONVERGENCE_IDENTIFIED`, hence NO SCORE.

**8. Contribution Calculation Semantics:**
- Each factor contribution is precisely its normalized `[0.0, 1.0]` value multiplied by its specific weight.
- `priority_score = gap_contribution + exposure_contribution + demand_contribution`.

**9. Score Range:**
- `[0.0, 1.0]` bounded strictly.

**10. Demand Bounding Policy:**
- Max saturation cap of 50 signals (`MAX_DEMAND_CAP = 50.0`). Prevents manipulation via signal flooding.
- Extraneous bursts above 50 simply yield `1.0` normalized demand.

**11. Evidence-Quality Behavior:**
- EXPLICITLY NOT IMPLEMENTED. The priority score relies purely on the quantitative metrics of the convergence identified.

**12. Urgency Behavior:**
- EXPLICITLY NOT IMPLEMENTED. Semantic interpretation captures urgency, but it is not weighted or active in the mathematical Priority Engine to avoid model hallucination affecting algorithmic priority.

**13. Unsupported-Sector Behavior:**
- Sectors lacking deterministic public gap mappings (e.g. non-WATER) cannot achieve `CONVERGENCE_IDENTIFIED` and therefore do not receive a fabricated priority score.

**14. Provenance/Version Requirements:**
- The engine propagates the exactly configured `PriorityWeights` version (`1.0.0-final`) into the output `priority_version`.
- Provenance remains traced to the upstream opportunity and its source signals/evidence.

**15. Exact Test Evidence:**
- `backend/tests/test_priority_engine.py` validates bounding, saturation limits, deterministic addition of factors, and eligibility conditions (only `CONVERGENCE_IDENTIFIED` triggers scoring).
- Total backend test suite: 197/197 passing.
