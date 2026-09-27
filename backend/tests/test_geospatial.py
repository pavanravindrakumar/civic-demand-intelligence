import pytest
import os
import json
import hashlib

def test_geospatial_raw_provenance():
    zip_path = "data/raw/geospatial/vb_soi_ap_geojson.zip"
    assert os.path.exists(zip_path), "Raw geospatial zip file must exist."

    with open(zip_path, "rb") as f:
        zip_hash = hashlib.sha256(f.read()).hexdigest()

    expected_hash = "ed6800c3993ed7c5ccfae39cbb89a2280bd209bd4bda3e3b08f3dd34a8151df8"
    assert zip_hash == expected_hash, "Raw zip file hash mismatch. Data integrity compromised."

def test_geospatial_validation_results():
    val_path = "data/validation/geospatial_validation.json"
    assert os.path.exists(val_path), "Validation json must exist."

    with open(val_path, "r", encoding="utf-8") as f:
        val = json.load(f)

    assert val["lgd_join_field"] == "vlcode", "GeoJSON must join on vlcode."
    assert val["invalid_geometries"] == 0, "No invalid geometries should exist."
    assert val["percentage_coverage"] > 99.0, "Coverage must exceed 99%."
    assert val["features_matched_to_lgd"] > 15000, "Should match majority of villages."

def test_geospatial_normalized_output():
    norm_path = "data/normalized/village_geometry.geojson"
    assert os.path.exists(norm_path), "Normalized GeoJSON must exist."

    with open(norm_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["type"] == "FeatureCollection"
    assert "crs" in data

    # Check first feature schema
    if data["features"]:
        feat = data["features"][0]
        assert feat["type"] == "Feature"
        assert "geometry" in feat
        assert "properties" in feat

        props = feat["properties"]
        assert "lgd_village_code" in props
        assert "source_attribution" in props
        assert "village_name" in props

        # Ensure raw properties are stripped
        assert "total_households" not in props
        assert "vlcode" not in props
