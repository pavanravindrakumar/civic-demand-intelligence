-- Canonical Normalized Village Base Table
-- Dataset: <CURRENT_ENV_DATASET>
-- Table: normalized_villages
-- Description: The foundational, deterministic normalized village dataset containing LGD hierarchy and reported JJM household exposure and water gaps.

CREATE TABLE IF NOT EXISTS `<PROJECT_ID>.<CURRENT_ENV_DATASET>.<BASE_TABLE>` (
    state STRING NOT NULL OPTIONS(description="State name"),
    district STRING NOT NULL OPTIONS(description="District name"),
    block STRING NOT NULL OPTIONS(description="Block name"),
    panchayat STRING NOT NULL OPTIONS(description="Gram Panchayat name"),
    village_name STRING NOT NULL OPTIONS(description="Village name from LGD or JJM fallback"),
    lgd_village_code STRING NOT NULL OPTIONS(description="Official LGD Village Code (Canonical ID)"),
    jjm_village_id STRING NOT NULL OPTIONS(description="JJM internal village ID"),
    households INT64 OPTIONS(description="Reported Total Households"),
    fhtc_house_connections INT64 OPTIONS(description="Reported Functional Household Tap Connections (FHTC)"),
    reported_household_gap INT64 OPTIONS(description="Reported gap between households and FHTC"),
    household_exposure INT64 OPTIONS(description="Proxy for citizen exposure (matches households)"),
    match_type STRING NOT NULL OPTIONS(description="Type of LGD join match (e.g. DIRECT_LGD_MATCH)"),
    data_valid BOOL NOT NULL OPTIONS(description="Boolean indicating whether numeric relationships in the source record were valid"),
    source_system_jjm STRING NOT NULL OPTIONS(description="Source system URL/ID for JJM data"),
    source_system_lgd STRING NOT NULL OPTIONS(description="Source system URL/ID for LGD data")
)
CLUSTER BY lgd_village_code, district;
