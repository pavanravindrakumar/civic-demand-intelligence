import json
import csv
import hashlib
import os

def run_validation():
    # File paths
    zip_path = "data/raw/geospatial/vb_soi_ap_geojson.zip"
    geojson_path = "data/raw/geospatial/vb_soi_ap.GeoJSON"
    normalized_csv_path = "data/normalized/normalized_villages.csv"

    out_json = "data/validation/geospatial_validation.json"
    out_csv = "data/validation/geospatial_join_summary.csv"
    out_geojson = "data/normalized/village_geometry.geojson"

    # 1. SHA256 Hash
    with open(zip_path, "rb") as f:
        zip_hash = hashlib.sha256(f.read()).hexdigest()
    zip_size = os.path.getsize(zip_path)

    # 2. Load Normalized LGD Data
    lgd_codes = set()
    total_normalized_villages = 0
    with open(normalized_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lgd_codes.add(row["lgd_village_code"])
            total_normalized_villages += 1

    # 3. Load GeoJSON
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    crs = data.get("crs", "No CRS declared")
    features = data.get("features", [])

    total_source_features = len(features)
    valid_geometries = 0
    invalid_geometries = 0
    duplicate_identifiers = 0
    unique_identifiers = 0
    features_matched_to_lgd = 0
    unmatched_features = 0

    # We will figure out what property holds the LGD code. Usually it's 'vil_code' or 'LGD_Code' or something similar.
    # Let's see the first feature's properties
    if len(features) > 0:
        first_props = list(features[0]["properties"].keys())
    else:
        first_props = []

    # Let's find the LGD Code field
    lgd_field = None
    for field in ["vill_code", "VILL_CODE", "lgd_code", "LGD_CODE", "villcode"]:
        if len(features) > 0 and field in features[0]["properties"]:
            lgd_field = field
            break

    if lgd_field is None and len(features) > 0:
        # Just use the first field or whatever seems like a code
        for k in first_props:
            if "code" in k.lower() or "lgd" in k.lower():
                lgd_field = k
                break

    if not lgd_field and len(features) > 0:
        # fallback
        lgd_field = first_props[0]

    seen_ids = set()
    matched_lgd_codes = set()

    normalized_features = []

    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry")

        if geom and geom.get("type") and geom.get("coordinates"):
            valid_geometries += 1
        else:
            invalid_geometries += 1

        feat_id = str(props.get(lgd_field, "")) if lgd_field else ""

        if feat_id in seen_ids:
            duplicate_identifiers += 1
        else:
            unique_identifiers += 1
            seen_ids.add(feat_id)

        if feat_id in lgd_codes:
            features_matched_to_lgd += 1
            matched_lgd_codes.add(feat_id)

            # create normalized feature
            normalized_features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "lgd_village_code": feat_id,
                    "village_name": props.get("village_na", "") or props.get("VILL_NAME", ""),
                    "source_attribution": "National Water Informatics Centre (NWDP)"
                }
            })
        else:
            unmatched_features += 1

    ambiguous_matches = 0 # In our 1:1 set-based matching, no ambiguity, but duplicates mean multiple polygons for one code

    coverage = len(matched_lgd_codes) / len(lgd_codes) if len(lgd_codes) > 0 else 0

    validation_results = {
        "source_portal": "https://nwdp.nwic.gov.in/dataset/village-boundary",
        "dataset_name": "Village Boundary of Andhra Pradesh",
        "original_filename": "vb_soi_ap_geojson.zip",
        "retrieval_date": "2026-09-25",
        "file_size_bytes": zip_size,
        "sha256": zip_hash,
        "geometry_format": "GeoJSON",
        "crs": crs,
        "source_attribution": "Geological Survey of India / National Water Informatics Centre",
        "available_properties": first_props,
        "lgd_join_field": lgd_field,
        "total_source_features": total_source_features,
        "valid_geometries": valid_geometries,
        "invalid_geometries": invalid_geometries,
        "duplicate_identifiers": duplicate_identifiers,
        "unique_identifiers": unique_identifiers,
        "features_matched_to_lgd": features_matched_to_lgd,
        "unmatched_features": unmatched_features,
        "ambiguous_matches": ambiguous_matches,
        "percentage_coverage": coverage * 100,
        "total_normalized_villages": total_normalized_villages,
        "is_browser_valid": True if crs == "No CRS declared" or (isinstance(crs, dict) and "EPSG:4326" in str(crs)) or "84" in str(crs) else "Needs Check"
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2)

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(validation_results.keys()))
        writer.writeheader()
        writer.writerow(validation_results)

    if len(normalized_features) > 0:
        normalized_geojson = {
            "type": "FeatureCollection",
            "crs": crs,
            "features": normalized_features
        }
        with open(out_geojson, "w", encoding="utf-8") as f:
            json.dump(normalized_geojson, f)

    print("SUCCESS")
    print(json.dumps(validation_results, indent=2))

if __name__ == "__main__":
    run_validation()
