import pytest
from app.data_pipeline import parse_lgd, parse_jjm, normalize_and_join
import os

# We will use temporary files for the tiny fixture
@pytest.fixture
def temp_lgd_file(tmp_path):
    content = """<?xml version="1.0"?>
<Workbook>
    <Worksheet>
        <Table>
            <Row><Data>Header1</Data></Row>
            <Row><Data>Header2</Data></Row>
            <Row><Data>Header3</Data></Row>
            <Row><Data>Header4</Data></Row>
            <Row><Data>Header5</Data></Row>
            <Row>
                <Data>1</Data><Data>101</Data><Data>Dist1</Data><Data>201</Data><Data>Block1</Data><Data>10001</Data><Data>1</Data><Data>Village One</Data>
            </Row>
            <Row>
                <Data>2</Data><Data>101</Data><Data>Dist1</Data><Data>201</Data><Data>Block1</Data><Data>10002</Data><Data>1</Data><Data>Village Two</Data>
            </Row>
        </Table>
    </Worksheet>
</Workbook>
    """
    p = tmp_path / "lgd.xls"
    p.write_text(content, encoding="utf-8")
    return str(p)

@pytest.fixture
def temp_jjm_file(tmp_path):
    content = """S.No.,District,Block,Panchayat,Village id,Village,House Holds,House Connection
1,Dist1,Block1,Panch1,V1,Village One [Village LGD Code : 10001],100,50
2,Dist1,Block1,Panch1,V2,Village Two [Village LGD Code : 10002],200,250
3,Dist1,Block1,Panch2,V3,Village Three [Village LGD Code : 99999],invalid,invalid
4,Dist1,Block1,Panch2,V4,Village Four [Village LGD Code : 10001],-5,10
"""
    p = tmp_path / "jjm.csv"
    p.write_text(content, encoding="utf-8")
    return str(p)

def test_parse_lgd(temp_lgd_file):
    data = parse_lgd(temp_lgd_file)
    assert len(data) == 2
    assert data[0]['lgd_village_code'] == '10001'
    assert data[1]['lgd_village_name'] == 'Village Two'

def test_parse_jjm(temp_jjm_file):
    data = parse_jjm(temp_jjm_file)
    assert len(data) == 4
    assert data[0]['jjm_lgd_village_code'] == '10001'
    assert data[0]['reported_total_households'] == 100
    assert data[2]['reported_FHTC'] == -1 # invalid numeric handling

def test_normalize_and_join(temp_lgd_file, temp_jjm_file):
    lgd = parse_lgd(temp_lgd_file)
    jjm = parse_jjm(temp_jjm_file)
    records, validation = normalize_and_join(lgd, jjm)

    assert len(records) == 4

    # Test valid row gap
    assert records[0]['reported_household_gap'] == 50
    assert records[0]['match_type'] == 'DIRECT_LGD_MATCH'
    assert records[0]['data_valid'] is True

    # Test FHTC > HH
    assert records[1]['reported_household_gap'] == 0 # max(hh-fhtc, 0)
    assert records[1]['data_valid'] is False

    # Test missing/invalid numeric
    assert records[2]['data_valid'] is False
    assert records[2]['match_type'] == 'UNMATCHED'

    # Test negative
    assert records[3]['data_valid'] is False

    # Validation checks
    assert validation['total_jjm_rows'] == 4
    assert validation['duplicate_lgd_in_jjm'] == 1 # 10001 is duplicated
    assert validation['direct_matches'] == 3 # V1, V2, V4 match LGD
    assert validation['unmatched'] == 1
