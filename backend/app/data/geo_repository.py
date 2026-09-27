import json
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
from pathlib import Path
import os
from typing import Optional, List, Dict, Any

# Project root is 4 levels above this file:
# backend/app/data/geo_repository.py -> backend/app/data -> backend/app -> backend -> project_root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_GEOJSON_PATH = _PROJECT_ROOT / "data" / "normalized" / "village_map.geojson"


class GeoRepository:
    def __init__(self, geojson_path: Optional[str] = None):
        # Resolve path: explicit argument overrides the default project-root-relative path.
        # Using __file__-relative resolution means the GeoJSON is found regardless of
        # which directory the uvicorn process is started from.
        if geojson_path is not None:
            self.geojson_path = geojson_path
        else:
            self.geojson_path = str(_DEFAULT_GEOJSON_PATH)

        if not os.path.exists(self.geojson_path):
            logger.warning(
                "GeoJSON not found at resolved path. "
                "Geo-dependent endpoints will return empty results. "
                "Expected location: data/normalized/village_map.geojson under project root."
            )
        self.features = []
        self._loaded = False

    def _load_data(self):
        if not self._loaded:
            if os.path.exists(self.geojson_path):
                try:
                    with open(self.geojson_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.features = data.get("features", [])
                except Exception as e:
                    logger.error("External data failure", extra={"safe_context": {"operation": "load_geo_data", "error_type": type(e).__name__}})
            self._loaded = True

    def get_villages(self, district: Optional[str] = None, block: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
        self._load_data()

        filtered = []
        for feat in self.features:
            props = feat.get("properties", {})

            if district and props.get("district") != district:
                continue
            if block and props.get("block") != block:
                continue

            filtered.append(feat)
            if len(filtered) >= limit:
                break

        return {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
                }
            },
            "features": filtered
        }

    def get_village(self, lgd_village_code: str) -> Optional[Dict[str, Any]]:
        self._load_data()

        for feat in self.features:
            props = feat.get("properties", {})
            if str(props.get("lgd_village_code")) == str(lgd_village_code):
                return feat
        return None

# Singleton instance
geo_repository = GeoRepository()
