import json
import csv
import os
from pyproj import Transformer
from shapely.geometry import shape, mapping

def build_map_geometry():
    in_geojson = "data/normalized/village_geometry.geojson"
    in_csv = "data/normalized/normalized_villages.csv"
    out_geojson = "data/normalized/village_map.geojson"

    # 1. Load CSV data to get District, Block, Panchayat
    village_data = {}
    with open(in_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            village_data[row["lgd_village_code"]] = {
                "district": row["district"],
                "block": row["block"],
                "panchayat": row["panchayat"]
            }

    # 2. Setup Transformer EPSG:7755 -> EPSG:4326
    # EPSG:7755 is Kalyanpur 1975 / India zone IIa
    # EPSG:4326 is WGS84
    transformer = Transformer.from_crs("EPSG:7755", "EPSG:4326", always_xy=True)

    # Function to recursively transform coordinates
    def transform_coords(coords, geom_type):
        if geom_type == "Point":
            return transformer.transform(coords[0], coords[1])
        elif geom_type in ["LineString", "MultiPoint"]:
            return [transformer.transform(x, y) for x, y in coords]
        elif geom_type in ["Polygon", "MultiLineString"]:
            return [[transformer.transform(x, y) for x, y in ring] for ring in coords]
        elif geom_type == "MultiPolygon":
            return [[[transformer.transform(x, y) for x, y in ring] for ring in poly] for poly in coords]
        else:
            return coords

    # 3. Load GeoJSON
    with open(in_geojson, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 4. Process Features
    simplified_features = []

    for feat in data.get("features", []):
        props = feat.get("properties", {})
        lgd_code = props.get("lgd_village_code")

        # Only include if we have the village in normalized_villages
        if not lgd_code or lgd_code not in village_data:
            continue

        geom = feat.get("geometry")
        if not geom:
            continue

        # Transform coords to WGS84
        geom_wgs84 = {
            "type": geom["type"],
            "coordinates": transform_coords(geom["coordinates"], geom["type"])
        }

        # Simplify geometry
        shapely_geom = shape(geom_wgs84)
        # 0.001 degrees is roughly 111 meters at equator, good for zoom-out views
        simplified_geom = shapely_geom.simplify(0.001, preserve_topology=True)

        # Reconstruct properties
        vdata = village_data[lgd_code]
        new_props = {
            "lgd_village_code": lgd_code,
            "village_name": props.get("village_name", ""),
            "district": vdata["district"],
            "block": vdata["block"],
            "panchayat": vdata["panchayat"]
        }

        simplified_features.append({
            "type": "Feature",
            "geometry": mapping(simplified_geom),
            "properties": new_props
        })

    # 5. Output optimized geojson
    out_data = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84" # WGS84
            }
        },
        "features": simplified_features
    }

    with open(out_geojson, "w", encoding="utf-8") as f:
        # Use separators=(',', ':') to eliminate whitespace and make it compact
        json.dump(out_data, f, separators=(',', ':'))

    print(f"Processed {len(simplified_features)} features.")
    print(f"Original size: {os.path.getsize(in_geojson) / 1024 / 1024:.2f} MB")
    print(f"Simplified size: {os.path.getsize(out_geojson) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    build_map_geometry()
