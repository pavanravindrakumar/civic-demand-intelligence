from fastapi import APIRouter, HTTPException, Depends, Path
from backend.app.data.analytics_repository import AnalyticsRepository, AnalyticsSummary
from backend.app.analytics.engine import PriorityResult

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Dependency injection for the repository
def get_analytics_repository() -> AnalyticsRepository:
    # Use a singleton pattern or just instantiate. Since it caches locally, we can
    # keep a global instance for the lifecycle of the FastAPI app to avoid reloading CSV.
    # We'll use a module-level variable for simplicity in this local MVP phase.
    return _repo_instance

_repo_instance = AnalyticsRepository()

@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(repo: AnalyticsRepository = Depends(get_analytics_repository)):
    """
    Returns the deterministic water analytics summary for the entire dataset.
    Suitable for dashboard overviews.
    """
    summary = repo.get_summary()
    return summary

@router.get("/village/{lgd_village_code}", response_model=PriorityResult)
def get_village_analytics(
    lgd_village_code: str = Path(..., pattern=r"^\d{6}$"),
    repo: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Returns the deterministic analytics and priority breakdown for a specific village.
    """
    result = repo.get_village_analytics(lgd_village_code)
    if not result:
        raise HTTPException(status_code=404, detail=f"Village with LGD code {lgd_village_code} not found or invalid.")
    return result
