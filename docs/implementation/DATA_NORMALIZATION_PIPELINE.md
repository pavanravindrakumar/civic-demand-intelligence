# Data Normalization Pipeline

**Status:** COMPLETE (Phase 5C.1)

## 1. Source Files & Provenance
- **LGD Source:** `data/raw/lgd/extracted/villageofSpecificState...xls`
  - *Provenance:* Extracted from `lgdirectory.gov.in` (XML SpreadsheetML format).
- **JJM Source:** `data/raw/jjm/List of PWS Villages.csv`
  - *Provenance:* Extracted from `ejalshakti.gov.in` (CSV format).
  - *Vintage:* Contains exactly 16,002 rows for the State of Andhra Pradesh.

## 2. Normalization Flow
1. **LGD Parsing:** XML SpreadsheetML elements are regex-parsed, extracting exactly the data rows mapping to District, Block, Village Code, and Village Name.
2. **JJM Parsing:** The official CSV export is parsed natively. The `Village` field strings (e.g. `ANIGERU [Village LGD Code : 586841]`) are regex-parsed to extract the numeric ID.
3. **Canonical Join:** A deterministic direct join is performed: `JJM.jjm_lgd_village_code == LGD.lgd_village_code`.
4. **Arithmetic Calculation:** House connection gaps are calculated.
5. **Quality Checks:** Invalid records (negatives, FHTC > HH) are flagged.

## 3. Canonical Schema (BigQuery-ready)
- `state`: STRING (e.g., 'Andhra Pradesh')
- `district`: STRING
- `block`: STRING
- `panchayat`: STRING
- `village_name`: STRING (Authoritative from LGD if matched, fallback to JJM raw name)
- `lgd_village_code`: STRING (Primary identity/join key)
- `jjm_village_id`: STRING
- `households`: INTEGER
- `fhtc_house_connections`: INTEGER
- `reported_household_gap`: INTEGER
- `household_exposure`: INTEGER
- `match_type`: STRING ('DIRECT_LGD_MATCH' or 'UNMATCHED')
- `data_valid`: BOOLEAN
- `source_system_jjm`: STRING
- `source_system_lgd`: STRING

## 4. Analytical Semantics & Proxies
- **`reported_household_gap`**: Selected as the deterministic water indicator. It is explicitly calculated as `max(households - fhtc_house_connections, 0)`. It is NOT an "absolute unmet water demand" or a population figure; it represents the reported infrastructure gap.
- **`household_exposure`**: This serves as a proxy metric because actual granular citizen population headcounts are not deterministically available in the dataset without risking heavy assumption drift.

## 5. Output Artifacts
- **Normalized Data:** `data/normalized/normalized_villages.csv`
- **Validation Report:** `data/validation/pipeline_validation.json`

## 6. Validation Rules & Result (Phase 5C.1 Execution)
- Expected JJM Row Count: `16,002` -> **PASS**
- LGD Extraction Success: `16,002` -> **PASS**
- Unmatched Records: `0` -> **PASS**
- Missing HH/FHTC: `0` -> **PASS**
- Negative Values: `0` -> **PASS**
- FHTC > HH: `0` -> **PASS**
- State Households: `9,553,387` -> **PASS**
- State FHTC: `7,261,892` -> **PASS**
- State Household Gap: `2,291,495` -> **PASS**

No records were fabricated, and no synthetic mappings were employed. The pipeline provides a 100% deterministic foundation.
