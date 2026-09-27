# Convergence Opportunity Contract

## 1. Overview
A `ConvergenceOpportunity` explicitly defines the intersection where verified citizen demand encounters a corresponding publicly reported infrastructure deficiency.

Crucially, **it represents a planning context, NOT a final project allocation or priority score.** It deliberately excludes arbitrary metrics like "funding required", "priority ranking", or "return on investment".

## 2. Model Structure
The `ConvergenceOpportunity` is heavily modeled around preserving exact provenance from both public and citizen streams without mathematically corrupting either.
- **opportunity_id**: Unique UUID identifier.
- **assessment_id**: Link back to the exact `UnmetDemandAssessment`.
- **lgd_village_code**: The strictly matched 6-digit geographic boundary. No fuzzy matching or unassigned boundaries are permitted.
- **convergence_state**: Deterministic outcome state of the intersection (see below).
- **scheme_status**: State of any existing government project interventions (e.g. `FUNDED`, `NOT_AVAILABLE`). Defaults to `NOT_AVAILABLE` when deterministic scheme data is absent.
- **Measurement Preservation**: The model holds `reported_household_gap`, `signal_count`, and `distinct_submitter_count` structurally isolated to prevent inappropriate arithmetic substitutions.

## 3. Convergence States
The engine determines convergence solely using evidence logic:
- `CONVERGENCE_IDENTIFIED`: Upstream citizen demand aligns perfectly with a documented household gap.
- `INCOMPLETE_CONVERGENCE`: Upstream demand and public records exist for the village, but the numbers clash (e.g., citizen water demand exists, but the public JJM data explicitly claims 0 household gap).
- `PUBLIC_EVIDENCE_ONLY`: Public data dictates a gap exists, but no validating citizen signal has been submitted.
- `DEMAND_WITHOUT_RELEVANT_PUBLIC_EVIDENCE`: Demand exists for a sector (e.g., roads, health) that the public JJM dataset does not map to, or demand for water exists for a village completely absent from public datasets.

## 4. Integrity and Exclusions
- **Geography**: All opportunities are bound to exact LGD codes.
- **Temporal Traceability**: Explicitly segregates `public_evidence_vintage` from `demand_aggregation_window_start`/`end`.
- **No Demographics**: Does not conflate `signal_count` into arbitrary "beneficiaries" or "affected population".
