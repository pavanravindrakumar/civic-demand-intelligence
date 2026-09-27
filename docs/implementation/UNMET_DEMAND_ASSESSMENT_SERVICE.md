# Unmet Demand Assessment Service

## 1. Overview
The `UnmetDemandAssessmentEngine` orchestrates the functional generation of Unmet Demand Assessments by loading deterministic inputs from the `AnalyticsRepository` (public infrastructure evidence) and `CitizenDemandEvidenceRepository` (citizen demand).

## 2. Dependency Injection and Architecture
- **Stateless Pipeline**: The engine itself carries no internal mutable data apart from injected dependencies and local tracking variables during a run.
- **Dependency Injected Respositories**: It strictly relies on injected repositories to ensure the complex data mapping can be entirely unit-tested using fast in-memory deterministic mock datasets.

## 3. Rebuild Semantics
Unmet Demand Assessments are derived artifacts.
- To guarantee idempotency, calling `run_assessment()` does not attempt to mutate or append to existing JSON lines. Instead, it computes the total current baseline of the world based on immutable source streams and **replaces** the local development JSONL artifact entirely (`unmet_demand_assessments.jsonl`).
- This mathematically guarantees that no duplicate assessments will stack up if the pipeline crashes midway or is triggered multiple times for the same time boundary.

## 4. Test Strategy
- Exhaustive permutation testing validates the core deterministic evidence state matrix (`DEMAND_SUPPORTED`, `PUBLIC_EVIDENCE_ONLY`, `DEMAND_WITHOUT_MATCHING_PUBLIC_EVIDENCE`, `NO_RELEVANT_PUBLIC_EVIDENCE`).
- Unit tests run completely offline and invoke zero Google Cloud APIs, BigQuery loads, or GenAI inferences.
