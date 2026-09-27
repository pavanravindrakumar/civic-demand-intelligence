import csv
import re
import json
import os
from typing import List, Dict, Any, Tuple

def parse_lgd(file_path: str) -> List[Dict[str, str]]:
    """Parse the SpreadsheetML/XML LGD village file."""
    with open(file_path, "r", encoding="utf-8") as f:
        lgd_raw = f.read()

    lgd_rows = re.findall(r'<Row.*?>(.*?)</Row>', lgd_raw, re.DOTALL)
    lgd_data = []
    # Headers are typically row 3, data starts at row 5 in this specific file format.
    # To make it safer, we skip until we find actual data rows with sufficient cells.
    for row_str in lgd_rows:
        cells = re.findall(r'<Data.*?>(.*?)</Data>', row_str, re.DOTALL)
        if len(cells) >= 8:
            # S.No (0), DistCode (1), DistName (2), SubDistCode (3), SubDistName (4), VillCode (5), Version (6), Name (7)
            village_code = cells[5].strip()
            if not village_code.isdigit():
                continue # Skip headers
            lgd_data.append({
                'lgd_district_name': cells[2].strip(),
                'lgd_block_name': cells[4].strip(),
                'lgd_village_code': village_code,
                'lgd_village_name': cells[7].strip()
            })
    return lgd_data

def parse_jjm(file_path: str) -> List[Dict[str, Any]]:
    """Parse the JJM CSV export."""
    jjm_records = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            if not row or len(row) < 8:
                continue

            raw_village = row[5]
            match = re.search(r'\[Village LGD Code\s*:\s*(\d+)\]', raw_village)
            jjm_lgd_code = match.group(1) if match else None

            try:
                hh = int(row[6])
            except ValueError:
                hh = -1

            try:
                fhtc = int(row[7])
            except ValueError:
                fhtc = -1

            jjm_records.append({
                'jjm_district': row[1],
                'jjm_block': row[2],
                'jjm_panchayat': row[3],
                'jjm_village_id': row[4],
                'jjm_village_raw': raw_village,
                'jjm_lgd_village_code': jjm_lgd_code,
                'reported_total_households': hh,
                'reported_FHTC': fhtc
            })
    return jjm_records

def normalize_and_join(lgd_data: List[Dict[str, str]], jjm_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Join JJM and LGD data, perform gap calculations, and emit validation metrics."""
    # Build LGD index
    lgd_index = {}
    duplicate_lgd_in_source = 0
    for row in lgd_data:
        code = row['lgd_village_code']
        if code in lgd_index:
            duplicate_lgd_in_source += 1
        else:
            lgd_index[code] = row

    normalized_records = []

    # Validation counters
    direct_match = 0
    unmatched = 0
    missing_hh_fhtc = 0
    negative_values = 0
    fhtc_gt_hh = 0
    duplicate_lgd_in_jjm = 0

    seen_jjm_lgd = set()

    total_hh = 0
    total_fhtc = 0
    total_gap = 0

    for jjm in jjm_data:
        lgd_code = jjm.get('jjm_lgd_village_code')

        # Check duplicates in JJM
        if lgd_code:
            if lgd_code in seen_jjm_lgd:
                duplicate_lgd_in_jjm += 1
            seen_jjm_lgd.add(lgd_code)

        hh = jjm.get('reported_total_households', -1)
        fhtc = jjm.get('reported_FHTC', -1)

        gap = -1
        is_valid = True

        if hh < 0 or fhtc < 0:
            missing_hh_fhtc += 1
            is_valid = False
            if hh < 0 and hh != -1: negative_values += 1
            if fhtc < 0 and fhtc != -1: negative_values += 1
        elif fhtc > hh:
            fhtc_gt_hh += 1
            is_valid = False
            gap = max(hh - fhtc, 0)
        else:
            gap = max(hh - fhtc, 0)

        if is_valid:
            total_hh += hh
            total_fhtc += fhtc
            total_gap += gap

        # Join
        match_type = "UNMATCHED"
        lgd_village_name = None
        if lgd_code and lgd_code in lgd_index:
            direct_match += 1
            match_type = "DIRECT_LGD_MATCH"
            lgd_village_name = lgd_index[lgd_code]['lgd_village_name']
        else:
            unmatched += 1

        record = {
            'state': 'Andhra Pradesh',
            'district': jjm['jjm_district'],
            'block': jjm['jjm_block'],
            'panchayat': jjm['jjm_panchayat'],
            'village_name': lgd_village_name if lgd_village_name else jjm['jjm_village_raw'],
            'lgd_village_code': lgd_code,
            'jjm_village_id': jjm['jjm_village_id'],
            'households': hh,
            'fhtc_house_connections': fhtc,
            'reported_household_gap': gap,
            'household_exposure': hh if hh >= 0 else None,
            'match_type': match_type,
            'data_valid': is_valid,
            'source_system_jjm': 'ejalshakti.gov.in',
            'source_system_lgd': 'lgdirectory.gov.in'
        }
        normalized_records.append(record)

    validation = {
        'total_jjm_rows': len(jjm_data),
        'total_lgd_rows': len(lgd_data),
        'extracted_lgd_codes': len([r for r in jjm_data if r['jjm_lgd_village_code']]),
        'duplicate_lgd_in_jjm': duplicate_lgd_in_jjm,
        'duplicate_lgd_in_source': duplicate_lgd_in_source,
        'direct_matches': direct_match,
        'unmatched': unmatched,
        'missing_hh_fhtc': missing_hh_fhtc,
        'fhtc_gt_hh': fhtc_gt_hh,
        'negative_values': negative_values,
        'total_state_hh': total_hh,
        'total_state_fhtc': total_fhtc,
        'total_state_gap': total_gap,
        'duplicate_output_records': len(normalized_records) - len(set(r['jjm_village_id'] for r in normalized_records))
    }

    return normalized_records, validation

def write_outputs(records: List[Dict[str, Any]], validation: Dict[str, Any], output_dir: str, val_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)

    if records:
        keys = records[0].keys()
        with open(os.path.join(output_dir, "normalized_villages.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)

    with open(os.path.join(val_dir, "pipeline_validation.json"), "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2)

def run():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    lgd_path = os.path.join(root, "data/raw/lgd/extracted/villageofSpecificState2026_09_24_17_20_25_939.xls")
    jjm_path = os.path.join(root, "data/raw/jjm/List of PWS Villages.csv")

    print("Parsing LGD...")
    lgd_data = parse_lgd(lgd_path)
    print("Parsing JJM...")
    jjm_data = parse_jjm(jjm_path)

    print("Normalizing and Joining...")
    records, validation = normalize_and_join(lgd_data, jjm_data)

    print("Writing outputs...")
    write_outputs(
        records,
        validation,
        os.path.join(root, "data/normalized"),
        os.path.join(root, "data/validation")
    )

    print("Validation Results:")
    for k, v in validation.items():
        print(f"{k}: {v}")

    if validation['direct_matches'] == 16002:
        print("PASS")
    else:
        print("WARNING: Validation didn't perfectly match expectations")

if __name__ == "__main__":
    run()
