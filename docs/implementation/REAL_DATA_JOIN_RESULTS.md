# Real Data Join Results

## Join Strategy
The JJM dataset successfully provides `[Village LGD Code : XXXXXX]` inside the Village field for the vast majority of records. We extract this into `jjm_lgd_village_code` and perform an authoritative direct relational join against LGD. No fuzzy matching is used for the primary dataset since direct identifiers are present.

## Direct Join Results
- **Source Rows:** 16002
- **DIRECT_LGD_MATCH:** 16002
- **UNMATCHED_LGD_CODE:** 0
- **DUPLICATE_LGD_CODE:** 0

**Direct-match percentage:** 100.00%
