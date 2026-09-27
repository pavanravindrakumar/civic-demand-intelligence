"""
Phase 10B-1 hardening tests.

Covers:
  - CORS configuration parsing (_parse_allowed_origins)
  - /api/health endpoint behavior (ok vs degraded)
  - Path resolution correctness for analytics_repository and geo_repository
  - requirements-dev.txt / requirements.txt separation
"""
import os
import pathlib
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ─── CORS Configuration Parsing ───────────────────────────────────────────────

def test_cors_single_origin():
    """A single origin in ALLOWED_ORIGINS is parsed correctly."""
    with patch.dict(os.environ, {"ALLOWED_ORIGINS": "https://example.run.app"}, clear=False):
        from backend.app.main import _parse_allowed_origins
        origins = _parse_allowed_origins()
    assert origins == ["https://example.run.app"]


def test_cors_multiple_origins():
    """Comma-separated origins are split and stripped correctly."""
    with patch.dict(
        os.environ,
        {"ALLOWED_ORIGINS": "https://a.run.app, https://b.run.app ,https://c.run.app"},
        clear=False,
    ):
        from backend.app.main import _parse_allowed_origins
        origins = _parse_allowed_origins()
    assert origins == ["https://a.run.app", "https://b.run.app", "https://c.run.app"]


def test_cors_empty_env_falls_back_to_localhost():
    """When ALLOWED_ORIGINS is not set, the local-development fallback is used."""
    env = {k: v for k, v in os.environ.items() if k != "ALLOWED_ORIGINS"}
    with patch.dict(os.environ, env, clear=True):
        from backend.app.main import _parse_allowed_origins
        origins = _parse_allowed_origins()
    assert origins == ["http://localhost:3000"]


def test_cors_whitespace_only_env_falls_back_to_localhost():
    """Whitespace-only ALLOWED_ORIGINS is treated as unset."""
    with patch.dict(os.environ, {"ALLOWED_ORIGINS": "   "}, clear=False):
        from backend.app.main import _parse_allowed_origins
        origins = _parse_allowed_origins()
    assert origins == ["http://localhost:3000"]


def test_cors_wildcard_is_not_in_default_origins():
    """The wildcard '*' must never appear in the parsed allowed origins."""
    env = {k: v for k, v in os.environ.items() if k != "ALLOWED_ORIGINS"}
    with patch.dict(os.environ, env, clear=True):
        from backend.app.main import _parse_allowed_origins
        origins = _parse_allowed_origins()
    assert "*" not in origins


# ─── Health Endpoint ──────────────────────────────────────────────────────────

def test_health_ok_when_data_loaded():
    """Health endpoint returns status=ok when all data repositories are loaded."""
    from app.main import app

    mock_summary = MagicMock()
    mock_summary.total_villages_analyzed = 100

    mock_repo = MagicMock()
    mock_repo.get_summary.return_value = mock_summary

    mock_geo = MagicMock()
    mock_geo.features = [{"type": "Feature"}]

    with patch("backend.app.api.analytics.get_analytics_repository", return_value=mock_repo), \
         patch("backend.app.data.geo_repository.geo_repository", mock_geo):
        client = TestClient(app)
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_health_degraded_when_analytics_empty():
    """Health endpoint returns status=degraded when analytics data is empty."""
    from app.main import app

    mock_summary = MagicMock()
    mock_summary.total_villages_analyzed = 0

    mock_repo = MagicMock()
    mock_repo.get_summary.return_value = mock_summary

    mock_geo = MagicMock()
    mock_geo.features = [{"type": "Feature"}]

    with patch("backend.app.api.analytics.get_analytics_repository", return_value=mock_repo), \
         patch("backend.app.data.geo_repository.geo_repository", mock_geo):
        client = TestClient(app)
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert "analytics_data_empty" in body["issues"]


def test_health_degraded_when_geo_empty():
    """Health endpoint returns status=degraded when GeoJSON data is empty."""
    from app.main import app

    mock_summary = MagicMock()
    mock_summary.total_villages_analyzed = 100

    mock_repo = MagicMock()
    mock_repo.get_summary.return_value = mock_summary

    mock_geo = MagicMock()
    mock_geo.features = []

    with patch("backend.app.api.analytics.get_analytics_repository", return_value=mock_repo), \
         patch("backend.app.data.geo_repository.geo_repository", mock_geo):
        client = TestClient(app)
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert "geo_data_empty" in body["issues"]


def test_health_response_does_not_expose_paths():
    """Health response must not contain filesystem paths in the body."""
    from app.main import app

    mock_summary = MagicMock()
    mock_summary.total_villages_analyzed = 0

    mock_repo = MagicMock()
    mock_repo.get_summary.return_value = mock_summary

    mock_geo = MagicMock()
    mock_geo.features = []

    with patch("backend.app.api.analytics.get_analytics_repository", return_value=mock_repo), \
         patch("backend.app.data.geo_repository.geo_repository", mock_geo):
        client = TestClient(app)
        response = client.get("/api/health")

    body_text = response.text
    # No filesystem paths should appear in the response
    assert "C:\\" not in body_text
    assert "/home/" not in body_text
    assert "normalized_villages" not in body_text
    assert "village_map.geojson" not in body_text


# ─── Path Resolution ──────────────────────────────────────────────────────────

def test_analytics_repository_uses_project_root_path():
    """AnalyticsRepository default CSV path is __file__-relative, not CWD-relative."""
    from backend.app.data.analytics_repository import _DEFAULT_CSV_PATH, _PROJECT_ROOT

    # The project root must be the civic-demand-intelligence directory
    assert _PROJECT_ROOT.name == "civic-demand-intelligence"

    # The default CSV path must be within the project root
    assert _DEFAULT_CSV_PATH.is_relative_to(_PROJECT_ROOT)

    # The path must end with the expected relative path
    assert str(_DEFAULT_CSV_PATH).endswith(
        str(pathlib.Path("data") / "normalized" / "normalized_villages.csv")
    )


def test_geo_repository_uses_project_root_path():
    """GeoRepository default GeoJSON path is __file__-relative, not CWD-relative."""
    from backend.app.data.geo_repository import _DEFAULT_GEOJSON_PATH, _PROJECT_ROOT

    # The project root must be the civic-demand-intelligence directory
    assert _PROJECT_ROOT.name == "civic-demand-intelligence"

    # The default GeoJSON path must be within the project root
    assert _DEFAULT_GEOJSON_PATH.is_relative_to(_PROJECT_ROOT)

    # The path must end with the expected relative path
    assert str(_DEFAULT_GEOJSON_PATH).endswith(
        str(pathlib.Path("data") / "normalized" / "village_map.geojson")
    )


def test_analytics_repository_accepts_explicit_path():
    """AnalyticsRepository accepts an explicit path argument (for test isolation)."""
    from backend.app.data.analytics_repository import AnalyticsRepository

    repo = AnalyticsRepository(csv_path="/nonexistent/path.csv")
    assert repo.csv_path == "/nonexistent/path.csv"


def test_geo_repository_accepts_explicit_path():
    """GeoRepository accepts an explicit path argument (for test isolation)."""
    from backend.app.data.geo_repository import GeoRepository

    repo = GeoRepository(geojson_path="/nonexistent/path.geojson")
    assert repo.geojson_path == "/nonexistent/path.geojson"


# ─── Dependency Separation ────────────────────────────────────────────────────

def test_pytest_not_in_production_requirements():
    """pytest must not appear in production requirements.txt."""
    req_path = pathlib.Path(__file__).resolve().parents[1] / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    content = req_path.read_text(encoding="utf-8").lower()
    assert "pytest" not in content, (
        "pytest found in production requirements.txt — it must be in requirements-dev.txt only"
    )


def test_dev_requirements_file_exists():
    """requirements-dev.txt must exist for local development setup."""
    dev_req_path = pathlib.Path(__file__).resolve().parents[1] / "requirements-dev.txt"
    assert dev_req_path.exists(), "requirements-dev.txt not found"


def test_dev_requirements_includes_pytest():
    """requirements-dev.txt must include pytest."""
    dev_req_path = pathlib.Path(__file__).resolve().parents[1] / "requirements-dev.txt"
    assert dev_req_path.exists(), "requirements-dev.txt not found"
    content = dev_req_path.read_text(encoding="utf-8").lower()
    assert "pytest" in content, "pytest not found in requirements-dev.txt"
