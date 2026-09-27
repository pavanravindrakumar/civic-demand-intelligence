import pytest
from google.genai import types

from backend.app.copilot.orchestrator import (
    ModelResponse,
    FunctionCallRequest,
    FunctionCallResponse
)
from backend.app.copilot.gemini_sdk_adapter import (
    parse_sdk_response,
    build_model_content,
    build_tool_content
)

def test_parse_sdk_text_only_response():
    resp = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[types.Part.from_text(text="Hello there")],
                    role="model"
                )
            )
        ]
    )
    model_resp = parse_sdk_response(resp)
    assert model_resp.text == "Hello there"
    assert len(model_resp.function_calls) == 0

def test_parse_sdk_single_function_call():
    fc = types.FunctionCall(
        id="fc-123",
        name="get_analytics_summary",
        args={}
    )
    resp = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[types.Part(function_call=fc)],
                    role="model"
                )
            )
        ]
    )
    model_resp = parse_sdk_response(resp)
    assert len(model_resp.function_calls) == 1
    assert model_resp.function_calls[0].id == "fc-123"
    assert model_resp.function_calls[0].name == "get_analytics_summary"
    assert model_resp.function_calls[0].args == {}

def test_parse_sdk_multiple_function_calls():
    fc1 = types.FunctionCall(id="fc-1", name="get_analytics_summary", args={})
    fc2 = types.FunctionCall(id="fc-2", name="get_village_analytics", args={"lgd_village_code": "123"})
    resp = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[
                        types.Part(function_call=fc1),
                        types.Part(function_call=fc2)
                    ],
                    role="model"
                )
            )
        ]
    )
    model_resp = parse_sdk_response(resp)
    assert len(model_resp.function_calls) == 2
    assert model_resp.function_calls[1].name == "get_village_analytics"
    assert model_resp.function_calls[1].args["lgd_village_code"] == "123"

def test_parse_sdk_empty_response():
    resp = types.GenerateContentResponse(candidates=[])
    model_resp = parse_sdk_response(resp)
    assert model_resp.text is None
    assert len(model_resp.function_calls) == 0

def test_build_model_content_preserves_function_calls():
    model_resp = ModelResponse(
        function_calls=[
            FunctionCallRequest(id="fc-1", name="get_analytics_summary", args={})
        ]
    )
    content = build_model_content(model_resp)
    assert content.role == "model"
    assert len(content.parts) == 1
    assert content.parts[0].function_call is not None
    assert content.parts[0].function_call.name == "get_analytics_summary"

def test_build_tool_content_from_success_response():
    tool_resp = FunctionCallResponse(
        id="fc-1",
        name="get_analytics_summary",
        result={"ready": True, "provenance_source": "JJM/LGD Analytics Dataset"},
        is_error=False
    )
    content = build_tool_content([tool_resp])
    assert content.role == "user"  # Google Gen AI expects user role for tool results
    assert len(content.parts) == 1
    assert content.parts[0].function_response is not None
    assert content.parts[0].function_response.name == "get_analytics_summary"
    assert content.parts[0].function_response.response["provenance_source"] == "JJM/LGD Analytics Dataset"
    assert content.parts[0].function_response.response["ready"] is True

def test_build_tool_content_from_error_response():
    tool_resp = FunctionCallResponse(
        id="fc-2",
        name="get_village_analytics",
        result={"error_category": "NOT_FOUND", "error_message": "Village not found"},
        is_error=True
    )
    content = build_tool_content([tool_resp])
    assert content.role == "user"
    assert content.parts[0].function_response.response["error_category"] == "NOT_FOUND"

def test_sdk_loop_serialization_round_trip():
    # Model returns FunctionCall
    fc = types.FunctionCall(id="test-id", name="get_analytics_summary", args={})
    sdk_resp = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[types.Part(function_call=fc)],
                    role="model"
                )
            )
        ]
    )

    # Adapter parses it
    model_resp = parse_sdk_response(sdk_resp)
    assert model_resp.function_calls[0].name == "get_analytics_summary"

    # Adapter builds content for next turn
    model_content = build_model_content(model_resp)
    assert model_content.role == "model"
    assert model_content.parts[0].function_call.name == "get_analytics_summary"

    # Tool executes and adapter builds tool content
    tool_resp = FunctionCallResponse(
        id="test-id",
        name="get_analytics_summary",
        result={"success": True}
    )
    tool_content = build_tool_content([tool_resp])
    assert tool_content.role == "user"
    assert tool_content.parts[0].function_response.name == "get_analytics_summary"
