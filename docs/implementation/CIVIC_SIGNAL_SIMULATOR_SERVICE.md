# Civic Signal Simulator Service

## 1. Overview
The `CivicSignalSimulator` handles the generation of deterministic, multilingual synthetic citizen signals based on a predefined scenario catalog.

## 2. Determinism and Idempotency
The service uses a predictable combination of `scenario_id`, `version`, and `seed` to generate signals.
- **Deterministic IDs**: `signal_id` and `idempotency_key` are constructed using SHA-256 hashing of the scenario parameters and the loop index.
- **Idempotency**: Running the identical scenario + seed + version configuration multiple times safely skips duplicate generation and does not bloat the repository.

## 3. Repository Interfaces
- **`AnalyticsRepository`**: Accessed read-only to deterministically select target villages for `POSITIVE_GAP` or `ZERO_GAP` scenarios based on actual JJM public evidence.
- **`SyntheticSignalRepository`**: Handles the append-only storage of the generated `StoredCitizenSignal` objects into a quarantined file (`synthetic_citizen_signals.jsonl`).

## 4. Multilingual Fixtures
The simulator cyclically selects from a fixture set of English and Telugu statements, ensuring a diverse linguistic sample without calling LLMs during generation. Semantic interpretation is deliberately deferred to the later `GeminiInterpreter` phase.

## 5. Pipeline Orchestration
The simulator is designed to be injected into the `SyntheticCivicIntelligenceOrchestrator`, which seamlessly connects the simulated signal generation step to the rest of the Civic Intelligence Pipeline (interpretation, demand aggregation, convergence, priority, and ledger). See `SYNTHETIC_CIVIC_INTELLIGENCE_PIPELINE.md` for complete end-to-end details.

## 6. API Exposure
This simulator and the encompassing orchestration pipeline are exposed safely to frontend clients via the Demo API. For details on how these scenarios are executed and constrained at the API boundary, see [DEMO_SCENARIO_API_CONTRACT.md](./DEMO_SCENARIO_API_CONTRACT.md).
