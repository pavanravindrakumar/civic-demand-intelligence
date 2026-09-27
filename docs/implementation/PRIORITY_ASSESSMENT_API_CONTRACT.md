# Priority Assessment API Contract

## 1. Endpoints

The API is strictly read-only and designed for UI consumption. It does not perform any calculations, mutations, or interactions with the GenAI layers.

- `GET /api/priority/assessments`
- `GET /api/priority/assessments/{priority_assessment_id}`

## 2. Supported Filters

For the collection endpoint, the following filters are supported (enforced strictly via server-side Pydantic validation):
- `lgd_village_code` (e.g. `111111`)
- `canonical_need_type` (e.g. `WATER_SUPPLY_DEFICIT`)
- `sector` (e.g. `WATER`)
- `priority_version` (e.g. `1.0.0-final`)
- `eligibility_status` (e.g. `CONVERGENCE_IDENTIFIED` or `PUBLIC_EVIDENCE_ONLY`)
- `limit` (Maximum 100 records, defaults to 50)

## 3. Score Semantics & Deterministic Ordering

By default, the collection endpoint orders results by `priority_score` (descending) and then `evaluated_at` (descending).
**Important Semantic Warning:** The ordering exposed by this API is purely an algorithmic sort of deterministically calculated convergence footprints. It **is not** a finalized political policy decision, a guaranteed ranking of funding, nor a statement of absolute importance.

## 4. Null / No-Score States

Assessments where the Priority Engine produces no score (such as `PUBLIC_EVIDENCE_ONLY`, `INCOMPLETE_CONVERGENCE`) are returned with:
- `priority_score = null`
- `factors = {}`
- `eligibility_status` preserving the exact upstream state causing the exclusion.

"No score" is treated as structurally different from a `0.0` score and is never coerced. The API guarantees it will not fabricate an explanation for excluded assessments.

## 5. Factor Explanation Boundary

The API returns a `factors` dictionary for `CONVERGENCE_IDENTIFIED` assessments that simplifies UI presentation by providing:
- `normalized_input`
- `configured_weight`
- `contribution`

### Active Factors
The active factors exactly match `1.0.0-final`:
- `infrastructure_gap` (derived from "Reported Household Tap-Connection Gap")
- `household_exposure` (derived from "Exposure Proxy")
- `validated_demand` (derived from "Validated Citizen Demand")

Inactive theoretical factors like **urgency** and **evidence quality** are not exposed as they have zero mathematical effect on the deterministic priority calculation.

## 6. Provenance & Evidence Chain

References to external provenance are securely exposed.
- `citizen_evidence_provenance`: Guaranteed to preserve synthetic context if applicable (e.g., `SYNTHETIC_DEMO_SIGNAL`).
- `public_evidence_provenance`: Preserves public data tags (e.g., `REAL_JJM_LGD`).

Detailed upstream record IDs are provided (`priority_assessment_id`, `opportunity_id`), allowing the UI to cross-reference the `Evidence Ledger API` for comprehensive audits without duplicating the entire ledger object into the priority endpoint.

## 7. Privacy & PII Safety

The API acts as a strict boundary. It **will never** expose:
- Raw citizen text or transcripts.
- Submitter pseudonyms or phone numbers.
- Underlying Gemini API keys, logic paths, or thought blocks.
- Inference assumptions about exact "beneficiaries" or real-world "population" (it strictly returns the `Exposure Proxy`).
- Calculations about funding requirements.
