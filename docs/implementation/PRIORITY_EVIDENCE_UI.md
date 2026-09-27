# Priority & Evidence Explanation UI Implementation

## 1. UI Data Flow

The `PriorityDecisionPanel` acts as the definitive decision-support surface when a policymaker selects an analytical village (via `HotspotMap` or `VillageLookup`).

1. **Selection:** LGD Village Code is selected in the parent map/lookup component.
2. **Priority Fetch:** `PriorityDecisionPanel` calls `GET /api/priority/assessments?lgd_village_code={code}` via the typed `api.ts` frontend client.
3. **Ledger Fetch:** If the policymaker clicks "View Evidence Ledger", the panel makes a secondary call to `GET /api/evidence/ledger/{priority_assessment_id}`.

All transformations, joins, and normalizations are explicitly handled by the backend API. The React layer strictly renders the deterministic API shapes without performing any math, recalculations, or interpretation.

## 2. API Dependencies

The frontend consumes two specific read-only API boundaries:
- `Priority Assessment API`
- `Evidence Ledger API`

These APIs are designed specifically to expose the exact mathematical outputs of the `1.0.0-final` Priority Engine version without leaking underlying PII or mutable operations.

## 3. Factor Explanation

For a scored assessment (`priority_score !== null`), the UI expands an exact "Why this surfaced?" breakdown of the active factors:

- **Infrastructure Gap**
- **Validated Citizen Demand**
- **Exposure Proxy**

For each factor, the UI displays exactly three deterministic properties provided by the backend:
1. `normalized_input`
2. `configured_weight`
3. `contribution`

## 4. No-Score Behavior

For records where the Priority Engine explicitly withheld a combined score (e.g., `PUBLIC_EVIDENCE_ONLY`, `INCOMPLETE_CONVERGENCE`):
- The API provides `priority_score: null`.
- The UI explicitly renders: `"No combined priority score available"`.
- It displays the `eligibility_status` causing the exclusion.
- It does **not** cast the score to `0` or `0.0`, protecting the semantic meaning of "not scored" versus "scored as zero."

## 5. Provenance Display & Distinctions

Synthetic demonstration signals and real public evidence are strictly visually separated.
- Synthetic citizen signals trigger a highly visible `SYNTHETIC DEMO CITIZEN EVIDENCE` tag based on `citizen_evidence_provenance === "SYNTHETIC_DEMO_SIGNAL"`.
- Real public infrastructure evidence triggers a `REAL / OFFICIAL PUBLIC EVIDENCE` tag based on `public_evidence_provenance`.
- The two streams are never conflated into a single "verified" badge.

## 6. Evidence Ledger Drill-Down

The "View Evidence Ledger" action expands an audit panel showing the exact, append-only history of the Priority Assessment. It displays:
- All related provenance IDs (Assessment ID, Convergence Opportunity ID, Unmet Demand ID).
- Absolute raw measurements at the time of evaluation (`reported_household_gap`, `household_exposure`, `signal_count`, `distinct_submitter_count`).
- A deterministic `record_hash` ensuring data integrity over time.

## 7. PII Boundary & Strict Constraints

The UI acts as a hard boundary for data privacy:
- It **does not** render raw text or messages.
- It **does not** render submitter pseudonyms.
- It **does not** render GenAI reasoning chains, thought blocks, or SDK signatures.
- It strictly relies on the aggregation metrics (e.g. `signal_count`).

## 8. Terminology

Terminology strictly adheres to the approved civic intelligence lexicon:
- **Reported Household Tap-Connection Gap**: Used exclusively over "absolute gap".
- **Validated Citizen Demand**: Used exclusively over "citizen requests".
- **Exposure Proxy**: Used exclusively over "Population", since it is an estimation and not an official census population metric.
- **Priority Score**: Used exclusively over "ranking" or "guaranteed recommendation".
