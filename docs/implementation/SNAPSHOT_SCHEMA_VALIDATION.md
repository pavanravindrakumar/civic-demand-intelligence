# Precomputed Snapshot Validation

## Schema Feasibility
Based on real data constraints and the simulation run, the snapshot table `snapshot_hotspot_summary` and `snapshot_district_intelligence` can successfully represent:
- **Geographic Identity:** YES (resolved to stable LGD `geography_id`)
- **Civic Need Category:** YES (from Gemini structured output)
- **Official Gap Metric:** YES (`total_households - fhtc_households`)
- **Priority Factors:** YES (Gap, Demand, Urgency, Quality)
- **Population/Context:** NO. Precise historical Census 2011 population data requires a complex village-level crosswalk that is not feasible for the 6-day MVP.
  - **Resolution:** We will use `total_households * 4.5` (average Indian household size) as a proxy for MVP Population Impact context. This is documented clearly in the deterministic priority calculation.
- **Evidence Confidence:** YES (Data states: AVAILABLE, PARTIAL, MISSING map accurately)
- **Synthetic Fraction:** YES (tracked through ledger)

## Scoring Validation (Factor Availability)
- **Gap Severity:** AVAILABLE (Directly from JJM Gap arithmetic)
- **Population Impact:** DERIVABLE (Derived from JJM `total_households` proxy)
- **Citizen Demand:** AVAILABLE (From pipeline deduplication)
- **Urgency:** AVAILABLE (From Gemini `CivicNeedExtraction`)
- **Evidence Quality:** AVAILABLE (From JJM missing data state)

All 5 priority factors can be deterministically computed using real available data fields.
