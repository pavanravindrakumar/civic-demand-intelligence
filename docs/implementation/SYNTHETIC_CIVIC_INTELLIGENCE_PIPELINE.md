# Synthetic Civic Intelligence Pipeline

## 1. Overview
The Synthetic Civic Intelligence Pipeline acts as the main orchestration loop that connects the `CivicSignalSimulator` offline synthetic signal generator to the complete deterministic backend evaluation engine. It enables offline testing and controlled hackathon demonstrations without contaminating real government public evidence.

## 2. Pipeline Flow
The orchestrator (`SyntheticCivicIntelligenceOrchestrator`) accepts a scenario specification and then systematically delegates to the core services using dependency injection. The architecture enforces zero business-logic duplication inside the orchestrator.

The flow executes in the following order:
1. **Simulator**: Spawns synthetic `StoredCitizenSignal` entries based on deterministic fixtures and an explicitly supplied `scenario_id`.
2. **Interpretation Service**: Converts signals to `CivicNeed`. During offline tests, a `MockInterpreter` maps phrases. For a live demo, a `GeminiInterpreter` will be injected.
3. **Demand Aggregation**: Groups validated needs by `canonical_need_type` and `lgd_village_code` within a defined time window.
4. **Unmet Demand**: Combines aggregated `CitizenDemandEvidence` with existing public JJM/LGD data into an `UnmetDemandAssessment`.
5. **Convergence**: Analyzes the assessment against convergence logic (e.g. gap > 0) to output a `ConvergenceOpportunity`.
6. **Priority**: Calculates deterministic scores based on weights if the convergence state is `CONVERGENCE_IDENTIFIED`.
7. **Evidence Ledger**: Persists immutable audit records summarizing the full derivation chain.

## 3. Provenance Boundaries
The orchestrator preserves strict isolation:
- The input signals are permanently stamped with `SYNTHETIC_DEMO_SIGNAL` provenance.
- The downstream pipeline results (demand, unmet demand, convergence, priority) are recorded against this synthetic data in local development stores only.
- The public evidence maintains its official `REAL_JJM_LGD` provenance.
- No synthetic records are written into `data/raw/` or `data/normalized/`. They live solely in `data/local_development/`.

## 4. Failure States & Idempotency
- **Idempotency**: Repeatedly executing the same `scenario_id` + `version` + `seed` skips generation and interpretation of already-processed records, thanks to idempotency keys.
- **Failures**: The orchestrator handles failures safely. If interpretation is skipped or fails, the pipeline exits gracefully. If a village lacks public gaps, the convergence engine outputs `INCOMPLETE_CONVERGENCE` and the priority engine correctly declines to score it, reflecting the true systemic response.

## 5. Offline Testing vs Live Execution
By leveraging Dependency Injection for the `SignalInterpreter`, we guarantee that tests can run entirely offline via `MockInterpreter`. A future injection step will swap this with `GeminiInterpreter` for one controlled, live run, preserving the exact same downstream mathematics.
