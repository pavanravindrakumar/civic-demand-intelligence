# Civic Need Interpretation Contract

## 1. Overview
This contract defines the safe boundary for transforming an already-received Citizen Signal into a canonical, evidence-preserving Civic Need representation. It enforces a strict separation between semantic interpretation (done by AI or mocks) and deterministic data handling (done by application code).

## 2. Canonical Models
The output of the interpretation process is tightly bound to two Pydantic models with `extra='forbid'` enforced:

* **`CivicNeedExtraction`**: The raw structured output produced by Gemini. Contains fields like `need_type`, `need_description` (max 500 chars), `location_expression`, `urgency`, and `detected_language`.
* **`CivicNeed`**: The canonical representation integrated into the broader data pipeline. Includes resolved mappings like `sector` and tracks data provenance (`source_signal_id`, `processing_version`).

## 3. Need Taxonomy
The interpreter strictly classifies needs into the MVP canonical taxonomy defined in the overarching data architecture:
* `WATER_SUPPLY_DEFICIT` (Sector: WATER)
* `WATER_QUALITY_ISSUE` (Sector: WATER)
* `ROAD_CONNECTIVITY_DEFICIT` (Sector: ROADS)
* `SANITATION_DEFICIT` (Sector: SANITATION)
* `ELECTRICITY_ACCESS_DEFICIT` (Sector: ELECTRICITY)
* `HEALTH_FACILITY_DEFICIT` (Sector: HEALTH)
* `EDUCATION_FACILITY_DEFICIT` (Sector: EDUCATION)
* `OTHER_DEVELOPMENT_NEED` (Sector: OTHER)

*If Gemini returns an unmapped or misspelled category, the schema validation fails closed, preventing data corruption.*

## 4. Multilingual Semantic Normalization
Different expressions of the same problem (e.g., "తాగునీరు సరిగా రావడం లేదు" in Telugu vs. "water is not coming properly" in English) are safely normalized to the single canonical taxonomy (e.g., `WATER_SUPPLY_DEFICIT`). The original input language is tracked via `detected_language`.

## 5. AI vs. Deterministic Boundary
**The interpreter is permitted to:**
* Parse unstructured text in any language.
* Match the text against the allowed `need_type` taxonomy.
* Extract a `location_expression` from the text as the citizen expressed it.
* Express an `urgency` tier.

**The interpreter is strictly FORBIDDEN from:**
* Inventing or resolving the 6-digit `lgd_village_code` directly.
* Calculating authoritative infrastructure gaps.
* Calculating a "priority score".
* Creating funding allocations or population estimates.
* Re-stating arbitrary unsupported metrics into the canonical response schema.

## 6. Voice and Messaging Readiness Boundaries
The boundary anticipates alternative channel integrations:
* **VOICE**: The interpreter requires the upstream intake process to provide a normalized text transcript in `raw_text`. It will cleanly reject interpretation if transcription is pending.
* **MESSAGING**: Identity and PII are stripped at intake. The interpreter does not expect, request, or parse phone numbers from the payload.

## 7. Interpreter Abstraction
The system utilizes a `SignalInterpreter` base class.
* `MockInterpreter`: Serves deterministic interpretation for offline pipeline testing and development.
* `GeminiInterpreter`: Serves as the implementation boundary for the real LLM.

### 7.1 Schema Adapter Boundary
To resolve serialization bugs in the SDK without weakening application security, the boundary operates via a schema adapter:

1. **Pydantic canonical model (`CivicNeedExtraction`)**: The single source of truth, enforcing `extra='forbid'`.
2. **JSON Schema adapter (`generate_gemini_json_schema`)**: Extracts the raw Python dictionary representation of the Pydantic JSON schema. This strictly preserves standard constraints like `additionalProperties: false`.
3. **Google Gen AI SDK (`response_json_schema`)**: The dictionary is passed directly into this schema endpoint, bypassing the SDK's automatic Pydantic serialization that fails with `ConfigDict(extra='forbid')`.
4. **Gemini structured JSON**: The model emits text conforming to the schema.
5. **Pydantic Validation**: The resulting text is parsed and validated by the unchanged `CivicNeedExtraction.model_validate` method. Gemini schema compliance is never treated as sufficient validation.
