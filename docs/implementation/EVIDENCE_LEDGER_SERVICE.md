# Evidence Ledger Service

## 1. Overview
The `EvidenceLedgerService` translates `PriorityAssessment` and `ConvergenceOpportunity` objects into secure, append-only `EvidenceLedgerEntry` objects without performing any novel mathematical calculation or civic inferences.

## 2. Repository Interface
- **Dependency Injection**: Relies on `EvidenceLedgerRepository`.
- **Idempotency Strategy**: Uses `priority_assessment_id` + `calculation_version` + `priority_version` as a composite key. If the engine emits the exact same assessment, the repository returns early without bloating the `.jsonl` file.
- **Conflict Strategy**: If the same composite key arrives with a conflicting `record_hash`, the repository raises a hard `ValueError`, failing closed to protect audit integrity.

## 3. Implementation Context
- The ledger currently targets `data/local_development/evidence_ledger.jsonl`.
- Unlike the deterministic snapshot generators (which overwrite `.tmp` files to present a clean current state), the ledger is explicitly designed to retain historical data and grow over time.
