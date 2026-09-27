# Real Data Gap Validation Results

## Normalization & Arithmetic
- **Field Mapping:** `House Holds` → `reported_total_households`, `House Connection` → `reported_FHTC`
- **Gap Calculation:** `reported_household_gap = reported_total_households - reported_FHTC`
- **Population Proxy:** Total households is explicitly labeled as `household_exposure`. It is NOT population.

## Validation Output
- **Valid Gap Records:** 16002
- **Invalid Numeric Relationships (e.g. FHTC > HH):** 0

## State-Level Aggregation
- **SUM(reported_total_households):** 9553387
- **SUM(reported_FHTC):** 7261892
- **SUM(reported_household_gap):** 2291495
