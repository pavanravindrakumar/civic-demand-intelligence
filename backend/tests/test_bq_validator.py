import pytest
import csv
from scripts.validate_bq_schema import validate_normalized_data
import os

@pytest.fixture
def base_csv(tmp_path):
    def make_csv(filename, rows):
        p = tmp_path / filename
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                'state', 'district', 'block', 'panchayat', 'village_name', 'lgd_village_code',
                'jjm_village_id', 'households', 'fhtc_house_connections', 'reported_household_gap',
                'household_exposure', 'match_type', 'data_valid', 'source_system_jjm', 'source_system_lgd'
            ])
            for r in rows:
                writer.writerow(r)
        return str(p)
    return make_csv

def test_valid_record(base_csv):
    path = base_csv("valid.csv", [[
        'AP', 'D1', 'B1', 'P1', 'V1', '1001', 'J1', '100', '50', '50', '100', 'DIRECT', 'True', 'jjm', 'lgd'
    ]])
    res = validate_normalized_data(path)
    assert res['status'] == 'PASS'
    assert res['total_rows'] == 1
    assert res['passed_checks'] == 1

def test_missing_column(tmp_path):
    p = tmp_path / "missing_col.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['state', 'district']) # clearly missing columns
    res = validate_normalized_data(str(p))
    assert res['status'] == 'FAIL'
    assert any("Missing required columns" in e for e in res['errors'])

def test_malformed_integer(base_csv):
    path = base_csv("bad_int.csv", [[
        'AP', 'D1', 'B1', 'P1', 'V1', '1001', 'J1', 'abc', '50', '50', '100', 'DIRECT', 'True', 'jjm', 'lgd'
    ]])
    res = validate_normalized_data(path)
    assert res['status'] == 'FAIL'
    assert res['invalid_type_count'] == 1

def test_malformed_boolean(base_csv):
    path = base_csv("bad_bool.csv", [[
        'AP', 'D1', 'B1', 'P1', 'V1', '1001', 'J1', '100', '50', '50', '100', 'DIRECT', 'Yes', 'jjm', 'lgd'
    ]])
    res = validate_normalized_data(path)
    assert res['status'] == 'FAIL'
    assert res['invalid_type_count'] == 1

def test_duplicate_lgd(base_csv):
    path = base_csv("dup_lgd.csv", [
        ['AP', 'D1', 'B1', 'P1', 'V1', '1001', 'J1', '100', '50', '50', '100', 'DIRECT', 'True', 'jjm', 'lgd'],
        ['AP', 'D1', 'B1', 'P1', 'V2', '1001', 'J2', '100', '50', '50', '100', 'DIRECT', 'True', 'jjm', 'lgd']
    ])
    res = validate_normalized_data(path)
    assert res['status'] == 'FAIL'
    assert res['duplicate_count'] == 1

def test_negative_household(base_csv):
    path = base_csv("neg_hh.csv", [[
        'AP', 'D1', 'B1', 'P1', 'V1', '1001', 'J1', '-100', '50', '50', '100', 'DIRECT', 'True', 'jjm', 'lgd'
    ]])
    res = validate_normalized_data(path)
    assert res['status'] == 'FAIL'
    assert any("Negative numeric" in e for e in res['errors'])

def test_fhtc_gt_hh(base_csv):
    path = base_csv("fhtc_gt_hh.csv", [[
        'AP', 'D1', 'B1', 'P1', 'V1', '1001', 'J1', '100', '150', '0', '100', 'DIRECT', 'True', 'jjm', 'lgd'
    ]])
    res = validate_normalized_data(path)
    assert res['status'] == 'FAIL'
    assert res['arithmetic_mismatch_count'] >= 1

def test_incorrect_gap(base_csv):
    path = base_csv("bad_gap.csv", [[
        'AP', 'D1', 'B1', 'P1', 'V1', '1001', 'J1', '100', '50', '999', '100', 'DIRECT', 'True', 'jjm', 'lgd'
    ]])
    res = validate_normalized_data(path)
    assert res['status'] == 'FAIL'
    assert res['arithmetic_mismatch_count'] == 1
    assert any("Math inconsistency" in e for e in res['errors'])
