from fastapi import APIRouter, Query, Path, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from backend.app.models.civic_need import NeedType, SectorType
from backend.app.data.demand_evidence_repository import demand_evidence_repository

router = APIRouter(prefix="/api/demand", tags=["Demand Evidence"])

class CitizenDemandEvidenceResponse(BaseModel):
    demand_id: str
    canonical_need_type: NeedType
    sector: SectorType
    lgd_village_code: Optional[str]
    aggregation_window_start: datetime
    aggregation_window_end: datetime
    signal_count: int
    distinct_submitter_count: int
    source_channels: List[str]
    latest_signal_at: datetime
    aggregation_version: str

@router.get("/evidence", response_model=List[CitizenDemandEvidenceResponse])
def get_demand_evidence(
    canonical_need_type: Optional[NeedType] = None,
    sector: Optional[SectorType] = None,
    lgd_village_code: Optional[str] = Query(None, pattern=r"^\d{6}$"),
    geography_status: Optional[str] = Query(None, pattern=r"^(RESOLVED|UNRESOLVED)$"),
    window_start: Optional[datetime] = None,
    window_end: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Retrieve derived citizen demand evidence.
    """
    all_evidence = demand_evidence_repository.load_all()
    filtered = []

    for agg in all_evidence:
        if canonical_need_type and agg.canonical_need_type != canonical_need_type:
            continue
        if sector and agg.sector != sector:
            continue
        if lgd_village_code and agg.lgd_village_code != lgd_village_code:
            continue

        if geography_status == "RESOLVED" and agg.lgd_village_code is None:
            continue
        if geography_status == "UNRESOLVED" and agg.lgd_village_code is not None:
            continue

        if window_start and agg.aggregation_window_start < window_start:
            continue
        if window_end and agg.aggregation_window_end > window_end:
            continue

        filtered.append(agg)

    # Deterministic sort: signal_count desc, lgd_village_code asc, canonical_need_type asc
    # Handle None lgd_village_code cleanly for sorting
    filtered.sort(
        key=lambda x: (
            -x.signal_count,
            x.lgd_village_code or "",
            x.canonical_need_type
        )
    )

    # Map to response model
    response = [
        CitizenDemandEvidenceResponse(**agg.model_dump())
        for agg in filtered[:limit]
    ]

    return response

@router.get("/evidence/{lgd_village_code}", response_model=List[CitizenDemandEvidenceResponse])
def get_village_demand_evidence(
    lgd_village_code: str = Path(..., pattern=r"^\d{6}$"),
    window_start: Optional[datetime] = None,
    window_end: Optional[datetime] = None,
):
    """
    Retrieve all demand aggregates explicitly resolved to a specific LGD village code.
    Different need types remain completely distinct in the response.
    Unresolved geography aggregates are explicitly excluded from this route.
    """
    all_evidence = demand_evidence_repository.load_all()
    filtered = []

    for agg in all_evidence:
        if agg.lgd_village_code != lgd_village_code:
            continue

        if window_start and agg.aggregation_window_start < window_start:
            continue
        if window_end and agg.aggregation_window_end > window_end:
            continue

        filtered.append(agg)

    # Deterministic sort
    filtered.sort(
        key=lambda x: (
            -x.signal_count,
            x.canonical_need_type
        )
    )

    return [CitizenDemandEvidenceResponse(**agg.model_dump()) for agg in filtered]
