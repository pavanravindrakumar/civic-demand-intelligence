# Evidence Ledger Contract

## 1. Overview
The Evidence Ledger establishes cryptographic auditability for the deterministic Civic Intelligence pipeline. It is NOT a scoring engine; its sole purpose is to provably record the exact factor contributions and provenance trail behind every `PriorityAssessment` output, preventing hidden LLM math or untraceable decisions.

## 2. Traceability Chain
Every `EvidenceLedgerEntry` links directly down the stack:
`PriorityAssessment` -> `ConvergenceOpportunity` -> `UnmetDemandAssessment`

It preserves the exact input measurements (`reported_household_gap`, `signal_count`) alongside the final mathematically bounded `priority_score`.

## 3. PII & LLM Data Boundary
The ledger explicitly **rejects** storing:
- `source_signal_id` strings mapping back to specific raw submissions.
- Hidden Gemini `thought_signatures` or raw LLM JSON outputs.
- Any demographic identifiers (e.g., pseudonymous submitter IDs individually listed).

It records the deterministic *aggregate* evidence only.

## 4. Integrity and Immutable Design
- **Hashing**: Each record calculates a deterministic SHA-256 `record_hash` covering its precise semantic facts, ensuring that any silent alteration of factor math would be detected.
- **Append-Only**: The repository supports appending records. It actively blocks conflicting duplicates and silently idempotently absorbs exact duplicates to prevent database bloat during parallel execution.
- **Version Isolation**: Bumping `priority_version` or `calculation_version` inherently creates a distinct ledger key, establishing a permanent historical paper trail of how the algorithm evaluated a village on a specific day under a specific version.
