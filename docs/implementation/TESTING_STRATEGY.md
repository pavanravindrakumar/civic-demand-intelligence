# Testing Strategy

> Civic Demand Intelligence & Planning Platform
> Status: **READY FOR ENGINEERING**

This document outlines the testing strategy required to validate the implementation of the frozen architecture.

*Note: This is a strategic planning document. Tests are not yet implemented.*

## 1. Automated Testing Layers

### 1.1 Contract Tests
- **Objective:** Ensure all inter-service and Pydantic schemas remain strictly aligned with documented contracts.
- **Scope:**
  - `CivicNeedExtraction` schema vs Gemini response schema.
  - Copilot tool input/output schemas vs backend `TOOL_REGISTRY`.
  - Frontend API expectations vs FastAPI response models.

### 1.2 Unit Tests
- **Geography Resolution:** Test the fuzzy matching algorithm with known edge cases (exact matches, typos, ambiguous names).
- **Deduplication:** Verify `idempotency_key` generation logic handles identical inputs consistently and different inputs uniquely.
- **Scoring Engine:** (Crucial) Assert that the deterministic priority formula computes exactly the expected outputs for a matrix of fixed inputs. Test edge bounds (e.g., saturation capping, missing data logic).

### 1.3 Data Validation Tests (Continuous)
- **Objective:** Ensure BigQuery data integrity post-ingestion.
- **Scope:** Run assertions mapped to `DATA_READINESS_GATE.md` (e.g., duplicate checks, NULL checks on critical fields, match percentage thresholds).

### 1.4 AI Integration Tests
- **Structured Output:** Mock Gemini API to return various JSON structures (valid, missing fields, hallucinated fields) to ensure Pydantic parsing behaves as expected.
- **Fallback Logic:** Force Gemini audio extraction failures to verify graceful degradation to the GCP STT fallback path.

## 2. Integration & System Tests

### 2.1 API & Snapshot Tests
- **Snapshot Integrity:** Verify that calling the `POST /api/admin/refresh-snapshots` endpoint correctly aggregates data from `gap_assessments` and `priority_assessments` into the snapshot tables.
- **Read-Only Asserts:** Ensure Copilot execution endpoints absolutely cannot modify database state.

### 2.2 Security & Authorization
- **Copilot Auth:** Verify endpoints reject requests missing valid Firebase tokens or with invalid roles.
- **Rate Limiting:** Simulate burst traffic to the signal submission endpoint to confirm 429 Too Many Requests responses.

## 3. Manual Verification & Smoke Tests

### 3.1 UI Smoke Tests
- Load dashboard, verify Hotspot List populates.
- Verify Map renders precomputed pins (no API errors).
- Open Intelligence Report, confirm all Evidence Ledger elements are visible.

### 3.2 End-to-End Demo Test
- **Objective:** Run the full "Golden Path" to guarantee the demo works flawlessly.
- **Path:**
  1. Submit synthetic voice signal via frontend.
  2. Verify signal appears in database with `is_synthetic=True`.
  3. Trigger snapshot refresh.
  4. Load dashboard, locate new signal in hotspot report.
  5. Open Copilot, ask a question about the specific hotspot.
  6. Verify Copilot grounds response in the exact tool output.

---
*Implementation Plan - Testing Strategy*
