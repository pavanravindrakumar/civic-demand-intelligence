# Data Join Results

## Join Strategy
JJM does not natively provide LGD codes. Join strategy utilizes a hierarchical deterministic match: State + District + Village Name, following normalization (lowercase, punctuation stripping, stopword removal).

When exact matches fail, the system relies on normalized matching (e.g. aligning "Y.S.R." to "YSR Kadapa", mapping "Ullamparu" to "Ullamparru", and stripping "(Rural)").

## Results (Pilot Subset Simulation)
- **EXACT_MATCH:** 2 (Palakollu Rural, Gorigapudi)
- **NORMALIZED_MATCH:** 5 (Ullamparu, Digamaru, Chinthakomma Dinne, Kopparthi, Gollapalli)
- **AMBIGUOUS:** 0
- **UNMATCHED:** 0
- **INVALID (Missing/Bad Data):** 1 (Unknown Village missing households)

**Match Percentage (Excluding Invalid):** 100.00%
