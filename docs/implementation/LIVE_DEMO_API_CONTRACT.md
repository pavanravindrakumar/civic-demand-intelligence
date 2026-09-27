# Live Demo API Contract

## 1. Overview
The Live Demo API (`POST /api/demo/scenarios/live/water-convergence`) is a controlled, single-village execution boundary used for real-time demonstration of the Civic Intelligence pipeline. Unlike the offline mock endpoint, this endpoint executes exactly ONE real Gemini API request to interpret a single synthetic signal.

## 2. Endpoint Contract

### `POST /api/demo/scenarios/live/water-convergence`

**Request:** (Empty body)
```json
{}
```

**Response Schema:**
```json
{
  "scenario_id": "WATER_CONVERGENCE",
  "simulation_version": "live-demo-v1.0",
  "pipeline_status": "COMPLETED",
  "ai_interpretation_mode": "LIVE GEMINI DEMONSTRATION",
  "gemini_request_count": 1,
  "gemini_model": "gemini-3.1-flash-lite",
  "canonical_need_type": "WATER_SUPPLY_DEFICIT",
  "detected_language": "te",
  "generated_signal_count": 1,
  "interpreted_need_count": 1,
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

## 3. Targeted Execution Scope
To meet strict performance requirements (O(k) runtime instead of O(N)), the live demo explicitly executes a **bounded single-village scenario**.
- The simulator deterministically selects a single LGD village.
- The pipeline execution scope is restricted (`targeted_execution=True`) to that exact village.
- The orchestrator will only process unmet demand, convergence, and priority evaluations for the selected village.
- The pipeline uses `upsert` semantics to persist the generated records locally, ensuring that the 30,000+ unrelated statewide artifacts remain unaffected by the ephemeral demonstration.

## 4. Controls & Security
- **Feature Flag:** Execution is gated behind `DEMO_LIVE_GEMINI_ENABLED=true`.
- **Server Control:** The browser/client CANNOT supply a custom prompt, model, LGD village, or dataset boundary.
- **Data Protection:** No BigQuery mutations, GCP writes, or PII exposures are permitted.
