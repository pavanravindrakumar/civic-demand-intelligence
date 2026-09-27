# Data Validation Results

## Overall Metrics
- **Total source rows (JJM):** 8
- **Unique entity keys:** 8
- **Duplicate keys:** 0
- **Missing required fields:** 1 (Total/FHTC)
- **Invalid numeric values:** 0
- **Impossible numeric relationships:** 0 (e.g., FHTC > Total)
- **Unmatched geography:** 0
- **Ambiguous geography:** 0
- **Exact matches:** 2
- **Normalized matches:** 5
- **Match Percentage:** 100.00%

## Gap Validation
- Calculated `gap_units = total_households - fhtc_households` for all 7 valid rows.
- Validated that `gap_units >= 0`.
- Compared `gap_units` against JJM's officially reported `Remaining Households`.
- **Result:** No discrepancies found in the pilot subset. The architecture's gap arithmetic aligns with the official JJM remaining households logic.

## Failures & Discrepancies
- JJM record "Unknown Village" in Y.S.R. Kadapa lacks numeric data for `total_households` and `fhtc_households`. This record maps to the `MISSING` quality tier and invalidates the gap calculation for that row.
