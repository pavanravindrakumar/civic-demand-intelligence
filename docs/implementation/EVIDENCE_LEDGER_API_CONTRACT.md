# Evidence Ledger API Contract

## 1. Overview
The Evidence Ledger API (`/api/evidence/ledger`) exposes the read-only audit layer of the Civic Intelligence pipeline. Its sole purpose is to provide policymakers with cryptographically hashed, untampered explanations for *why* a village received a particular priority score without revealing citizen PII.

## 2. Strict Boundary Rules
- **No Calculations**: The API does NOT recalculate demand, gap ratios, or priority scores. It strictly acts as a file reader surfacing existing derived JSON lines.
- **No Mutations**: There are no `POST`, `PUT`, `PATCH`, or `DELETE` methods. The ledger is immutable.
- **No PII**: The returned entries do not contain raw citizen text, phone numbers, or submitter pseudonym IDs. Demand evidence is strictly exposed via aggregate `signal_count` and `distinct_submitter_count`.

## 3. Endpoints

### `GET /api/evidence/ledger`
Retrieves a paginated list of ledger entries.
**Deterministic Filters:**
- `lgd_village_code` (e.g. `111111`)
- `canonical_need_type` (e.g. `WATER_SUPPLY_DEFICIT`)
- `sector` (e.g. `WATER`)
- `priority_version` (e.g. `priority-v1`)
- `calculation_version` (e.g. `convergence-v1`)
- `limit` (max 100, default 50)

**Ordering:**
Results are consistently returned sorted by `generated_at` (descending) and `ledger_entry_id` (ascending).

### `GET /api/evidence/ledger/{priority_assessment_id}`
Retrieves the specific exact audit entries explaining a priority assessment.
- Returns an array (though idempotency generally prevents duplicate identical records per assessment ID).
- Returns `404 Not Found` gracefully if the assessment lacks an audit trail.

## 4. Factor Explainability
The response explicitly preserves the `factor_contributions` and `factor_inputs_normalized` blocks injected by the Priority Engine. This provides mathematical explainability for the resulting `priority_score` without requiring LLMs to guess the engine's behavior.

## 5. Security & Isolation
The API explicitly refuses to return internal implementation details, raw SDK objects, or AI thought signatures. The deterministic `record_hash` (SHA-256) is provided for verification.
