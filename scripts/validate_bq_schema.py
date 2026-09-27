import csv
import sys
import os
import json

REQUIRED_COLUMNS = [
    'state', 'district', 'block', 'panchayat', 'village_name', 'lgd_village_code',
    'jjm_village_id', 'households', 'fhtc_house_connections', 'reported_household_gap',
    'household_exposure', 'match_type', 'data_valid', 'source_system_jjm', 'source_system_lgd'
]

def validate_normalized_data(filepath: str) -> dict:
    validation = {
        'schema_version': 'v1',
        'dataset_validated': filepath,
        'status': 'PASS',
        'total_rows': 0,
        'passed_checks': 0,
        'failed_checks': 0,
        'warnings': 0,
        'duplicate_count': 0,
        'invalid_type_count': 0,
        'null_count': 0,
        'arithmetic_mismatch_count': 0,
        'unique_lgd_codes': 0,
        'total_households': 0,
        'total_fhtc': 0,
        'total_gap': 0,
        'errors': []
    }

    lgd_codes = set()

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        headers = list(reader.fieldnames or [])
        missing_cols = set(REQUIRED_COLUMNS) - set(headers)
        extra_cols = set(headers) - set(REQUIRED_COLUMNS)

        if missing_cols:
            validation['errors'].append(f"Missing required columns: {missing_cols}")
            validation['status'] = 'FAIL'
            validation['failed_checks'] += 1
            return validation

        if extra_cols:
            validation['errors'].append(f"Unexpected columns detected: {extra_cols}")
            validation['status'] = 'FAIL'
            validation['failed_checks'] += 1
            return validation

        for row_num, row in enumerate(reader, start=2):
            validation['total_rows'] += 1
            row_failed = False

            # Null/Empty checks for required non-nullable string fields
            for field in ['state', 'district', 'block', 'panchayat', 'village_name', 'lgd_village_code', 'jjm_village_id', 'match_type', 'source_system_jjm', 'source_system_lgd']:
                if not row.get(field) or str(row[field]).strip() == "":
                    validation['errors'].append(f"Row {row_num}: {field} is empty or null.")
                    validation['null_count'] += 1
                    row_failed = True

            # Key validation
            lgd_code = row['lgd_village_code']
            if not lgd_code.isdigit():
                validation['errors'].append(f"Row {row_num}: Invalid LGD code format '{lgd_code}'.")
                validation['invalid_type_count'] += 1
                row_failed = True

            if lgd_code in lgd_codes:
                validation['errors'].append(f"Row {row_num}: Duplicate LGD village code '{lgd_code}'.")
                validation['duplicate_count'] += 1
                row_failed = True
            lgd_codes.add(lgd_code)

            # Numeric and Boolean checks
            try:
                hh = int(row['households'])
                fhtc = int(row['fhtc_house_connections'])
                gap = int(row['reported_household_gap'])

                exp_str = row['household_exposure']
                exp = int(exp_str) if exp_str else None

                if hh < 0 or fhtc < 0 or gap < 0:
                    validation['errors'].append(f"Row {row_num}: Negative numeric values found.")
                    validation['invalid_type_count'] += 1
                    row_failed = True

                if fhtc > hh:
                    validation['errors'].append(f"Row {row_num}: FHTC ({fhtc}) > HH ({hh}).")
                    validation['arithmetic_mismatch_count'] += 1
                    row_failed = True

                # Math consistency check
                if gap != (hh - fhtc):
                    validation['errors'].append(f"Row {row_num}: Math inconsistency. gap={gap}, hh={hh}, fhtc={fhtc}")
                    validation['arithmetic_mismatch_count'] += 1
                    row_failed = True

                if not row_failed:
                    validation['total_households'] += hh
                    validation['total_fhtc'] += fhtc
                    validation['total_gap'] += gap
            except ValueError:
                validation['errors'].append(f"Row {row_num}: Invalid numeric value found.")
                validation['invalid_type_count'] += 1
                row_failed = True

            # Boolean check
            if row['data_valid'] not in ['True', 'False', 'true', 'false']:
                validation['errors'].append(f"Row {row_num}: Invalid boolean in data_valid '{row['data_valid']}'")
                validation['invalid_type_count'] += 1
                row_failed = True

            if row_failed:
                validation['failed_checks'] += 1
                validation['status'] = 'FAIL'
            else:
                validation['passed_checks'] += 1

    validation['unique_lgd_codes'] = len(lgd_codes)
    return validation

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py validate_bq_schema.py <path_to_normalized_csv>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    result = validate_normalized_data(path)

    val_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "validation")
    os.makedirs(val_dir, exist_ok=True)
    out_path = os.path.join(val_dir, "bq_schema_validation.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Validation complete. Status: {result['status']}")
    print(f"Results written to {out_path}")
    if result['status'] == 'FAIL':
        sys.exit(1)
