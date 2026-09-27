import csv
import sys
import os
import json

from backend.app.analytics.engine import CivicAnalyticsEngine, PriorityWeights, VillageInput, ReadinessState

def run_local_analytics(filepath: str):
    engine = CivicAnalyticsEngine(PriorityWeights())

    results = {
        'rows_processed': 0,
        'valid_rows': 0,
        'invalid_rows': 0,
        'gap_total': 0,
        'records_requiring_missing_demand': 0,
        'calculation_version': engine.CALCULATION_VERSION
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results['rows_processed'] += 1

            try:
                hh = int(row['households'])
                fhtc = int(row['fhtc_house_connections'])
                gap = int(row['reported_household_gap'])

                inp = VillageInput(
                    lgd_village_code=row['lgd_village_code'],
                    households=hh,
                    fhtc_house_connections=fhtc,
                    reported_household_gap=gap,
                    validated_citizen_demand_count=None, # Explicitly missing
                    data_valid=row['data_valid'].lower() == 'true'
                )

                res = engine.assess_village(inp)

                if res.readiness == ReadinessState.INVALID_INPUTS:
                    results['invalid_rows'] += 1
                else:
                    results['valid_rows'] += 1
                    results['gap_total'] += res.reported_household_gap

                if res.readiness == ReadinessState.PUBLIC_EVIDENCE_ONLY:
                    results['records_requiring_missing_demand'] += 1

            except ValueError:
                results['invalid_rows'] += 1

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py run_local_analytics.py <csv_path>")
        sys.exit(1)

    res = run_local_analytics(sys.argv[1])
    print(json.dumps(res, indent=2))
