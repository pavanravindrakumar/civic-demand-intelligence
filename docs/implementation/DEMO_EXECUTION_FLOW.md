# Demo Execution Flow

> Civic Demand Intelligence & Planning Platform
> Status: **READY FOR ENGINEERING**

This document defines the exact, step-by-step rehearsal script for the hackathon prototype submission demo. Engineering must ensure this specific "Golden Path" is perfectly stable.

## Pre-Flight Checklist
- `min-instances=1` set on Cloud Run services (no cold starts).
- Database seeded with 5-10 synthetic signals to create initial hotspots.
- `snapshot_hotspot_summary` refreshed.
- Demo environment variables (`ENVIRONMENT=demo`, etc.) verified.

---

## Part 1: The Policymaker Dashboard (3 Minutes)
*Demonstrating the deterministic intelligence and trust layer.*

1. **Login:** Present the login screen. Authenticate as a Policymaker via Firebase Auth.
2. **Dashboard Overview:**
   - Highlight the split view: Map on the left, Hotspot List on the right.
   - Point out that the list is the operationally reliable primary interface.
   - Point out the `[DEMO MODE]` badge if active.
3. **Hotspot Selection:** Click on the highest-priority district (e.g., West Godavari or YSR Kadapa) in the list.
4. **Intelligence Report Breakdown:**
   - Scroll through the `IntelligenceReport` view.
   - Point out the **Reported Household Tap-Connection Gap** (derived from JJM).
   - Point out the **Deterministic Priority Score** and its factor breakdown (Gap, Pop, Demand, Urgency, Quality). Emphasize: *AI did not calculate this score.*
5. **Evidence Ledger & Trust:**
   - Expand the Evidence Ledger section.
   - Show the provenance chain: Signal received -> Need extracted -> Geography resolved -> JJM queried -> Gap calculated.
   - Highlight the visual badges: `[OFFICIAL EVIDENCE]`, `[SYNTHETIC]`.

## Part 2: Planning Copilot (2 Minutes)
*Demonstrating read-only, grounded AI assistance.*

1. **Open Copilot:** Open the chat interface next to the intelligence report.
2. **First Query (JJM Status):**
   - Ask: *"What is the exact Jal Jeevan Mission status for this district?"*
   - Show the response.
   - **Crucial step:** Show the Copilot audit log/debug view proving it called the `get_jjm_scheme_status` tool and executed a read-only query against the precomputed snapshot, rather than inventing numbers.
3. **Second Query (Policy Exploration):**
   - Ask: *"How would this district's priority change if we weighted citizen demand twice as heavily?"*
   - Show Copilot calling `compare_policy_weights` and presenting the deterministic recalculation.

## Part 3: The Citizen Voice (1 Minute)
*Demonstrating the upstream pipeline and multimodal ingestion.*

1. **Switch Context:** Open a mobile-emulated browser view to the Citizen Portal.
2. **Multilingual Voice Submission:**
   - Press the microphone button.
   - Speak a synthetic complaint in Telugu (or Hindi/English) about water supply.
   - Submit.
3. **Confirmation:** Show the immediate feedback: `signal_id` and "Report received." Emphasize that no PII was collected.
4. **Pipeline Conclusion:** Briefly explain that this audio goes directly to Gemini Multimodal (or STT fallback), extracts the structured need, updates the demand count, and automatically triggers the snapshot refresh to update the policymaker dashboard.

---
*Implementation Plan - Demo Execution Flow*
