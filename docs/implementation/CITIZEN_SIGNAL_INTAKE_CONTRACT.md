# Citizen Signal Intake Contract

## 1. Overview
The Citizen Signal Intake API establishes the secure boundary for receiving unprocessed civic demands from citizens. It is strictly separated from AI interpretation (Civic Need) and deterministic scoring, accepting and storing raw signals cleanly and idempotently according to the Canonical Data Contract.

## 2. Endpoint Configuration
* **Route:** `POST /api/citizen-signals`
* **Purpose:** Safely receive, deduplicate, and persist incoming citizen signals without synchronous AI interpretation or PII leakage.

## 3. Request Schema
The endpoint accepts a canonical `CitizenSignalRequest`:

```json
{
  "source": "TEXT",
  "raw_content": "We need a hospital in Addateegala.",
  "language_hint": "en",
  "is_synthetic": false,
  "idempotency_key": "optional-client-hash",
  "lgd_village_code": "586842"
}
```

* **Source Semantics:** Must be one of `TEXT`, `VOICE`, `MESSAGING`, `SIMULATOR`, `WEB_FORM`, `API`. Future voice and messaging integrations will adapt to this boundary without requiring schema overrides.
* **Geography Behavior:** If a 6-digit `lgd_village_code` is provided, it is validated purely on format length. The endpoint does *not* do fuzzy geocoding. If not provided, it is left `null` for future deterministic resolution.

## 4. Response Schema
```json
{
  "signal_id": "uuid-v4-string",
  "status": "RECEIVED",
  "is_synthetic": false,
  "submitted_at": "2026-09-25T13:00:00Z",
  "estimated_processing_time": "5-30 seconds",
  "reference_message": "Signal received; interpretation pending."
}
```
* **Status Semantics:** Returns `RECEIVED`, acknowledging storage. Does not claim "Civic Need Resolved".

## 5. Idempotency Behavior
* The system honors client-provided `idempotency_key` strings.
* If a duplicate key is submitted, the API returns `201 Created` with the existing `signal_id` and does *not* create a new database row.
* If no key is provided, the server securely hashes `(source + current_minute + first_20_chars)` as a fallback deterministic key.

## 6. PII Minimization
* **Strict Restriction:** The API purposely lacks `name`, `phone`, `email`, or `caste` fields. Identity attributes are explicitly rejected by Pydantic validation if attempted.
* **Pseudonymization:** Submissions are attached to a server-generated `submitter_pseudonym` (UUID) in the data store. No identity is linked.

## 7. Local Development Persistence
* During the no-cloud MVP phase, valid signals are appended natively to a JSONL file at `data/local_development/signals.jsonl`.
* This file is purposely isolated from `data/raw/` to ensure government datasets and citizen signals do not co-mingle.
* The persistence abstraction `SignalRepository` can be easily substituted for a BigQuery writer later.
