# Controlled Synthetic Civic Intelligence Demo API

## 1. Overview

This API exposes a strictly bounded demonstration endpoint for executing synthetic civic intelligence scenarios. It acts as an integration harness to demonstrate the deterministic capabilities of the pipeline (Signal → Need → Demand → Unmet Demand → Convergence → Priority → Ledger) without making live calls to Google Gemini, executing real data writes, or exposing PII.

## 2. Endpoint Contract

### `POST /api/demo/scenarios/run`

**Request Schema:**
```json
{
  "scenario_id": "WATER_CONVERGENCE", // Must be a supported ScenarioType
  "simulation_version": "demo-v1.0", // Optional, defaults to demo-v1.0
  "seed": "demo-seed-default",       // Optional, deterministic seed
  "batch_size": 5                    // Optional, bounded 1-50
}
```

**Allowed Scenarios:**
- `WATER_CONVERGENCE`: End-to-end matching of water needs with JJM footprint.
- `WATER_NO_PUBLIC_GAP`: Demand exists, but infrastructure is reported as complete.
- `NON_WATER_DEMAND`: Civic needs outside the currently supported JJM taxonomy.
- `UNRESOLVED_GEOGRAPHY`: Signals that lack identifiable LGD codes.

**Response Schema:**
```json
{
  "scenario_id": "WATER_CONVERGENCE",
  "simulation_version": "demo-v1.0",
  "pipeline_status": "COMPLETED",
  "ai_interpretation_mode": "DEMO / DETERMINISTIC MOCK",
  "generated_signal_count": 5,
  "interpreted_need_count": 5,
  "demand_evidence_count": 1,
  "unmet_demand_assessment_count": 1,
  "convergence_opportunity_count": 1,
  "priority_assessment_count": 1,
  "evidence_ledger_count": 1,
  "citizen_evidence_provenance": "SYNTHETIC_DEMO_SIGNAL",
  "public_evidence_provenance": "REAL_JJM_LGD",
  "error_stage": null,
  "error_code": null
}
```

## 3. Strict Execution Boundaries

- **Zero Gemini Requests:** This endpoint enforces a deterministic `MockInterpreter` configuration. It performs **ZERO** live language model inferences.
- **Zero Real World Ingestion:** No actual citizen input can be routed through this endpoint.
- **Zero Cloud Modification:** No BigQuery mutations or GCP operations are executed. All synthetic data resides in local `data/local_development/` repositories.
- **Strict Identity Boundaries:** PII (such as raw signal text or submitter pseudonyms) is never surfaced through the response summary.

## 4. Provenance Distinctions

The API strictly delineates synthetic data from real public data, returning:
- `citizen_evidence_provenance = SYNTHETIC_DEMO_SIGNAL`
- `public_evidence_provenance = REAL_JJM_LGD`

These labels inform the UI and ensure synthetic outputs are never misrepresented as real verified citizen evidence.

## 5. Failure & Idempotency States

- If a scenario is invalid, the API returns a structured HTTP `422 Unprocessable Entity` validation error.
- Internal orchestration errors return an HTTP `500` with a controlled JSON error payload `{ "detail": { "status": "FAILED", "stage": "<Stage Name>" } }`, explicitly masking any Python stack traces or internal mechanics.
- The pipeline execution maintains the underlying repository's idempotency. Running the same scenario with the same seed will yield a deterministic artifact flow.
