import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.data.geo_repository import geo_repository
import json
import os

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_geo_data(tmp_path):
    # Create mock geojson for testing
    mock_data = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [80.0, 15.0]},
                "properties": {
                    "lgd_village_code": "586842",
                    "village_name": "Addateegala",
                    "district": "Alluri Sitharama Raju",
                    "block": "ADDATEEGALA",
                    "panchayat": "ADDATEEGALA"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [80.1, 15.1]},
                "properties": {
                    "lgd_village_code": "586841",
                    "village_name": "Anigeru",
                    "district": "Alluri Sitharama Raju",
                    "block": "ADDATEEGALA",
                    "panchayat": "ADDATEEGALA"
                }
            }
        ]
    }

    # Save to a tmp path and redirect repo
    test_file = tmp_path / "test_village_map.geojson"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)

    old_path = geo_repository.geojson_path
    geo_repository.geojson_path = str(test_file)
    geo_repository._loaded = False

    yield

    geo_repository.geojson_path = old_path
    geo_repository._loaded = False

def test_get_geo_villages():
    response = client.get("/api/geo/villages")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 2

def test_get_geo_villages_limit():
    response = client.get("/api/geo/villages?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["features"]) == 1

def test_get_geo_villages_filter_district():
    response = client.get("/api/geo/villages?district=Alluri Sitharama Raju")
    assert response.status_code == 200
    data = response.json()
    assert len(data["features"]) == 2

    response2 = client.get("/api/geo/villages?district=Unknown")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["features"]) == 0

def test_get_geo_village_by_code():
    response = client.get("/api/geo/villages/586842")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "Feature"
    assert data["properties"]["lgd_village_code"] == "586842"

def test_get_geo_village_not_found():
    response = client.get("/api/geo/villages/999999")
    assert response.status_code == 404

def test_get_geo_hotspots_sorting_and_join():
    response = client.get("/api/geo/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"

    # We should have up to 2 features depending on the mock analytics join,
    # but the mock analytics repo is using the real CSV or a mocked one.
    # We need to mock the analytics repo behavior for this test to be fully isolated.
    # The current repo reads from data/normalized/normalized_villages.csv.
    # Since this is an integration test, it will join with real analytics.
    # Let's just assert the schema and sorting.
    features = data["features"]
    if len(features) > 1:
        gap0 = features[0]["properties"]["reported_household_gap"]
        gap1 = features[1]["properties"]["reported_household_gap"]
        assert gap0 >= gap1
        if gap0 == gap1:
            code0 = features[0]["properties"]["lgd_village_code"]
            code1 = features[1]["properties"]["lgd_village_code"]
            assert code0 < code1

    if len(features) > 0:
        props = features[0]["properties"]
        assert "reported_household_gap" in props
        assert "priority_score" in props
        assert "evidence_quality" in props
        # priority_score might be null if PUBLIC_EVIDENCE_ONLY, which is exactly what we want to verify.
        if props["readiness"] == "PUBLIC_EVIDENCE_ONLY":
            assert props["priority_score"] is None

def test_get_geo_hotspots_limit():
    response = client.get("/api/geo/hotspots?limit=1")
    assert response.status_code == 200
    assert len(response.json()["features"]) == 1

def test_get_geo_hotspots_validation():
    response = client.get("/api/geo/hotspots?limit=5000")
    # Pydantic validation should block > 1000
    assert response.status_code == 422
