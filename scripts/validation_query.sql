SELECT
  count(*) as total_rows,
  count(distinct lgd_village_code) as distinct_lgd_village_codes,
  countif(lgd_village_code is null or village_name is null) as invalid_required_identifier_count,
  countif(households < 0) as invalid_household_count,
  countif(fhtc_house_connections < 0) as invalid_fhtc_count,
  countif(fhtc_house_connections > households) as fhtc_greater_than_households_count,
  countif(reported_household_gap != (households - fhtc_house_connections)) as gap_arithmetic_mismatch_count,
  sum(households) as total_households,
  sum(fhtc_house_connections) as total_fhtc,
  sum(reported_household_gap) as total_reported_household_gap
FROM civic-intelligence-hackathon.civic_intelligence.normalized_villages
