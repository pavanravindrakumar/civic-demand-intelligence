# Convergence Opportunity Service

## 1. Overview
The `ConvergenceOpportunityEngine` translates mathematically validated `UnmetDemandAssessment` objects into strictly typed `ConvergenceOpportunity` records. It operates purely as a deterministic rules engine over structured evidence states.

## 2. Dependencies and Inputs
- **UnmetDemandRepository**: The explicit source of truth for the Unmet Demand Assessment derived data.
- **ConvergenceOpportunityRepository**: The destination for derived Convergence Opportunities.

*Note: In the MVP, JJM scheme status data is not deterministically available via a standalone repository. Therefore, the engine explicitly injects `NOT_AVAILABLE` for scheme status rather than inventing planning status.*

## 3. Idempotency and Persistence
- **Derived Artifact**: Convergence opportunities are treated as derived artifacts (i.e. effectively materialized views).
- **Atomic Replacement**: The `ConvergenceOpportunityEngine` does NOT append to or modify existing JSON lines. Instead, when `evaluate_opportunities()` is executed, it recalculates the entire current landscape and performs an atomic overwrite of `data/local_development/convergence_opportunities.jsonl`.
- This ensures that duplicate processing runs or interrupted executions cannot bloat the convergence mapping.

## 4. Testing
- Testing relies exclusively on Dependency Injection (`MockUnmetDemandRepo`, `MockConvergenceRepo`) inside `backend/tests/test_convergence_engine.py`.
- Evaluates the core convergence state logic (e.g. converting `DEMAND_SUPPORTED` with `gap > 0` into `CONVERGENCE_IDENTIFIED` versus converting `DEMAND_SUPPORTED` with `gap == 0` into `INCOMPLETE_CONVERGENCE`).
- No live Gemini calls, database mutations, or BigQuery executions occur.
