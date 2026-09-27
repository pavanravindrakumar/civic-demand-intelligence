from fastapi import APIRouter, Query, Path, HTTPException, Depends
from typing import Optional, Any, Dict
from backend.app.data.geo_repository import geo_repository
from backend.app.api.analytics import get_analytics_repository
from backend.app.data.analytics_repository import AnalyticsRepository

router = APIRouter(prefix="/api/geo", tags=["geo"])

@router.get("/villages", response_model=Dict[str, Any])
def get_geo_villages(
    district: Optional[str] = Query(None, description="Filter by district name"),
    block: Optional[str] = Query(None, description="Filter by block name"),
    limit: int = Query(1000, description="Max number of features to return", le=10000)
):
    """
    Retrieve lightweight GeoJSON map representation of villages.
    Filters out features based on district or block.
    """
    data = geo_repository.get_villages(district=district, block=block, limit=limit)
    return data

@router.get("/villages/{lgd_village_code}", response_model=Dict[str, Any])
def get_geo_village(lgd_village_code: str = Path(..., pattern=r"^\d{6}$")):
    """
    Retrieve geometry for a specific village by LGD code.
    """
    feature = geo_repository.get_village(lgd_village_code)
    if not feature:
        raise HTTPException(status_code=404, detail="Village geometry not found or unavailable")
    return feature

@router.get("/hotspots", response_model=Dict[str, Any])
def get_geo_hotspots(
    district: Optional[str] = Query(None, description="Filter by district name"),
    block: Optional[str] = Query(None, description="Filter by block name"),
    limit: int = Query(100, description="Max number of hotspot features to return", le=1000),
    repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Retrieve deterministic map hotspots based on Reported Household Tap-Connection Gap.
    Sorts descending by gap, then ascending by lgd_village_code.
    """
    # 1. Get all geographic features matching the filter (no limit here so we can sort globally)
    # The max villages in a district is usually < 2000, and state is 16k.
    # geo_repository is fast in-memory list. We pass a large limit to get all matching.
    geo_data = geo_repository.get_villages(district=district, block=block, limit=20000)
    features = geo_data.get("features", [])

    joined_features = []

    # 2. Join with Analytics
    for feat in features:
        props = feat.get("properties", {})
        lgd_code = props.get("lgd_village_code")

        analytics_res = repo.get_village_analytics(lgd_code)
        if not analytics_res:
            continue

        # Create a new feature dict to avoid mutating the cached repository feature
        new_feat = {
            "type": feat["type"],
            "geometry": feat["geometry"],
            "properties": {
                **props,
                "reported_household_gap": analytics_res.reported_household_gap,
                "household_exposure": analytics_res.household_exposure,
                "evidence_quality": analytics_res.evidence_quality.value,
                "readiness": analytics_res.readiness.value,
                "priority_score": analytics_res.priority_score
            }
        }
        joined_features.append(new_feat)

    # 3. Sort deterministically: reported_household_gap DESC, lgd_village_code ASC
    joined_features.sort(
        key=lambda x: (-x["properties"]["reported_household_gap"], x["properties"]["lgd_village_code"])
    )

    # 4. Enforce server-side limit
    sliced_features = joined_features[:limit]

    return {
        "type": "FeatureCollection",
        "crs": geo_data.get("crs"),
        "features": sliced_features
    }
