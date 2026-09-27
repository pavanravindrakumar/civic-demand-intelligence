import pytest
from pydantic import ValidationError
from google.genai import types

from backend.app.copilot.gemini_client import (
    GeminiConfig,
    GeminiProviderMode,
    get_client,
    get_generate_content_config,
    convert_to_orchestrator_call,
    convert_to_sdk_response
)
from backend.app.copilot.orchestrator import FunctionCallResponse
from backend.app.copilot.tools import ReadinessOutput

def test_developer_api_configuration_succeeds():
    config = GeminiConfig(
        gemini_model="gemini-3.1-flash-lite",
        provider_mode=GeminiProviderMode.DEVELOPER_API,
        api_key="test-key-not-real"
    )
    assert config.gemini_model == "gemini-3.1-flash-lite"
    assert config.api_key == "test-key-not-real"

def test_developer_api_fails_when_key_missing():
    with pytest.raises(ValidationError, match="api_key is required"):
        GeminiConfig(
            gemini_model="gemini-3.1-flash-lite",
            provider_mode=GeminiProviderMode.DEVELOPER_API
        )

def test_vertex_ai_configuration_succeeds_without_api_key():
    config = GeminiConfig(
        gemini_model="gemini-3.1-pro-preview",
        provider_mode=GeminiProviderMode.VERTEX_AI,
        google_cloud_project="civic-intelligence-hackathon",
        google_cloud_location="global"
    )
    assert config.gemini_model == "gemini-3.1-pro-preview"
    assert config.google_cloud_project == "civic-intelligence-hackathon"
    assert config.api_key is None

def test_vertex_ai_requires_project_and_location():
    with pytest.raises(ValidationError, match="google_cloud_project and google_cloud_location are required"):
        GeminiConfig(
            gemini_model="gemini-3.1-pro-preview",
            provider_mode=GeminiProviderMode.VERTEX_AI,
            google_cloud_project="civic-intelligence-hackathon"
        )

def test_api_key_not_allowed_in_vertex_mode():
    with pytest.raises(ValidationError, match="API Key must not be configured"):
        GeminiConfig(
            gemini_model="gemini-3.1-pro-preview",
            provider_mode=GeminiProviderMode.VERTEX_AI,
            google_cloud_project="civic-intelligence-hackathon",
            google_cloud_location="global",
            api_key="test-key-not-real"
        )

def test_developer_api_client_factory():
    config = GeminiConfig(
        gemini_model="gemini-3.1-flash-lite",
        provider_mode=GeminiProviderMode.DEVELOPER_API,
        api_key="test-key-not-real"
    )
    client = get_client(config)
    assert client is not None

def test_vertex_ai_client_factory():
    config = GeminiConfig(
        gemini_model="gemini-3.1-pro-preview",
        provider_mode=GeminiProviderMode.VERTEX_AI,
        google_cloud_project="test-project",
        google_cloud_location="us-central1"
    )
    client = get_client(config)
    assert client is not None

def test_generate_content_config_tool_compatibility():
    config = get_generate_content_config()

    assert len(config.tools) == 1
    tool = config.tools[0]

    tool_names = [d.name for d in tool.function_declarations]
    assert "get_analytics_summary" in tool_names
    assert "get_village_analytics" in tool_names

    assert getattr(config, "automatic_function_calling", None) is None
    assert config.tool_config.function_calling_config.mode.name == "AUTO"

def test_function_call_conversion():
    fc = types.FunctionCall(
        id="fc-123",
        name="get_village_analytics",
        args={"lgd_village_code": "586842"}
    )
    req = convert_to_orchestrator_call(fc)
    assert req.id == "fc-123"
    assert req.name == "get_village_analytics"
    assert req.args["lgd_village_code"] == "586842"

def test_function_response_conversion_preserves_result():
    fcr = FunctionCallResponse(
        id="fc-123",
        name="get_village_analytics",
        result={
            "data": {"lgd_village_code": "586842"},
            "provenance_source": "JJM/LGD Analytics Dataset"
        },
        is_error=False
    )
    part = convert_to_sdk_response(fcr)
    assert part.function_response is not None
    assert part.function_response.name == "get_village_analytics"

def test_error_function_response_preserves_error_category():
    fcr = FunctionCallResponse(
        id="fc-error",
        name="get_analytics_summary",
        result={
            "error_category": "NOT_FOUND",
            "error_message": "Not found"
        },
        is_error=True
    )
    part = convert_to_sdk_response(fcr)
    assert part.function_response.response["error_category"] == "NOT_FOUND"

def test_no_credential_values_in_serialized_config():
    config = GeminiConfig(
        gemini_model="gemini-3.1-flash-lite",
        provider_mode=GeminiProviderMode.DEVELOPER_API,
        api_key="test-key-not-real"
    )
    config_dict = config.model_dump()
    assert "api_key" not in config_dict
