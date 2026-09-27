import os
from fastapi import FastAPI
from backend.app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.analytics import router as analytics_router
from backend.app.api.copilot import router as copilot_router
from backend.app.api.geo import router as geo_router
from backend.app.api.signals import router as signals_router
from backend.app.api.demand_evidence import router as demand_router
from backend.app.api.evidence_ledger_api import router as ledger_router
from backend.app.api.priority_api import router as priority_router
from backend.app.api.demo_api import router as demo_router
from backend.app.api.middleware import (
    SecurityHeadersMiddleware,
    RequestIdMiddleware,
    RequestSizeMiddleware
)


def _parse_allowed_origins() -> list[str]:
    """
    Parse ALLOWED_ORIGINS from environment.

    In production: set ALLOWED_ORIGINS to a comma-separated list of trusted
    frontend origins, e.g.:
        ALLOWED_ORIGINS=https://civic-frontend-hash.run.app,https://my-custom-domain.example.com

    In local development: set ALLOWED_ORIGINS=http://localhost:3000
    or leave unset to use the default development fallback.

    The wildcard "*" is intentionally NOT supported to prevent accidental
    production misconfiguration.
    """
    raw = os.environ.get("ALLOWED_ORIGINS", "")
    if raw.strip():
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        return origins

    # Safe local-development fallback when the variable is not set.
    # In production (Cloud Run), ALLOWED_ORIGINS MUST be set explicitly.
    return ["http://localhost:3000"]


app = FastAPI(title="Civic Demand Intelligence API")

# CORS configuration driven entirely by the ALLOWED_ORIGINS environment variable.
# allow_credentials=False (default) is intentional: no authentication is implemented
# in this phase, so credentials are neither sent nor needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept", "X-Request-ID"],
)

app.add_middleware(RequestSizeMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)

app.include_router(analytics_router)
app.include_router(copilot_router)
app.include_router(geo_router)
app.include_router(signals_router)
app.include_router(demand_router)
app.include_router(ledger_router)
app.include_router(priority_router)
app.include_router(demo_router)


@app.get("/api/health")
def health_check():
    """
    Readiness health check.

    Returns HTTP 200 with status='ok' when all required application data is
    loaded and the service can serve requests.

    Returns HTTP 200 with status='degraded' when one or more required data
    sources failed to load. The caller should treat a degraded response as
    a signal that data-dependent endpoints may return empty or incorrect results.

    Deliberately does NOT expose filesystem paths, secrets, or internal
    configuration values in the response.
    """
    from backend.app.api.analytics import get_analytics_repository
    from backend.app.data.geo_repository import geo_repository

    issues: list[str] = []

    # Check analytics data (CSV-backed in-memory repository)
    try:
        repo = get_analytics_repository()
        summary = repo.get_summary()
        if summary.total_villages_analyzed == 0:
            issues.append("analytics_data_empty")
    except Exception:
        issues.append("analytics_data_unavailable")

    # Check geospatial data (GeoJSON-backed in-memory repository)
    try:
        geo_repository._load_data()
        if not geo_repository.features:
            issues.append("geo_data_empty")
    except Exception:
        issues.append("geo_data_unavailable")

    if issues:
        logger.warning("Health check degraded", extra={"safe_context": {"issues": issues}})
        return {"status": "degraded", "issues": issues}

    return {"status": "ok"}
