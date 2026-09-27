# Civic Need Interpretation Service

## 1. Overview
The `CivicNeedInterpretationService` is a reusable, programmatic application boundary responsible for orchestrating the Citizen Signal to Civic Need pipeline. It connects deterministic intake validation to external AI semantics.

**Pipeline Flow:**
```text
CitizenSignal
      ↓
CivicNeedInterpretationService
      ↓
SignalInterpreter (Injected abstraction, e.g. Mock/Gemini)
      ↓
Validated CivicNeed Extraction
      ↓
CivicNeedRepository (Local JSONL persistence)
```

## 2. Core Responsibilities
- **AI vs. Deterministic Boundary**: Orchestrates the handoff from a `StoredCitizenSignal` to the `SignalInterpreter`. It leaves semantic classification to the Interpreter and schema validation to Pydantic, enforcing that the Interpreter’s results conform to the canonical taxonomy without attempting to manually override semantics.
- **Dependency Injection**: Takes an interpreter (`SignalInterpreter`) and a persistence mechanism (`CivicNeedRepository`). This enables full offline testing using `MockInterpreter`.
- **Status Updates**: Directly updates the `extraction_status` on the `StoredCitizenSignal` (`INTERPRETED`, `FAILED`) without silently swallowing unrecoverable model errors.
- **Idempotency & Duplicate Prevention**: Checks `CivicNeedRepository` to ensure duplicate `CivicNeed` entities are not generated for the same successfully processed `source_signal_id`.

## 3. Persistence
In this phase, interpreted needs are written to a lightweight, append-only JSONL repository (`data/local_development/civic_needs.jsonl`).
- Raw AI payloads, API secrets, and intermediate tool structures are explicitly **NOT** persisted.
- Data lineage is maintained via `source_signal_id` preserving exactly the original signal identity.

## 4. Multi-Need and Channel Boundaries
- **Voice/Messaging Boundaries**: The service correctly refuses to interpret `VOICE` inputs that lack transcribed text and `MESSAGING` inputs that lack raw content. No transcription implementation is added here.
- **Multi-Need State**: The service retains the interpreter's boolean `is_multi_need` determination natively within the standard `CivicNeed` response.

## 5. Architectural Non-Goals
This service operates purely as programmatic business logic. It does not:
- Block or hook into `POST /api/citizen-signals`.
- Perform any AI operations itself.
- Resolve any geographic LGD codes or coordinate bounds.
- Introduce messaging queues, Pub/Sub, or complex distributed locking.
