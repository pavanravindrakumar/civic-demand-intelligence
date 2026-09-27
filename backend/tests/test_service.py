import pytest
from unittest.mock import MagicMock, patch
from google.genai import types

from backend.app.copilot.gemini_client import GeminiConfig, GeminiProviderMode
from backend.app.copilot.service import GeminiModelAdapter, GeminiCopilotService
from backend.app.copilot.orchestrator import ConversationTurn

@pytest.fixture
def mock_config():
    return GeminiConfig(
        gemini_model="gemini-3.1-flash-lite",
        provider_mode=GeminiProviderMode.DEVELOPER_API,
        api_key="fake-key"
    )

@patch("backend.app.copilot.service.get_client")
def test_adapter_text_response(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Mock the SDK GenerateContentResponse
    mock_client.models.generate_content.return_value = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[types.Part.from_text(text="I am a copilot")],
                    role="model"
                )
            )
        ]
    )

    adapter = GeminiModelAdapter(mock_config)
    history = [ConversationTurn(role="user", content="Who are you?")]

    model_resp = adapter.generate_response(history)
    assert model_resp.text == "I am a copilot"
    assert len(model_resp.function_calls) == 0

@patch("backend.app.copilot.service.get_client")
def test_service_single_function_call(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Setup mock to return a function call first, then text
    fc = types.FunctionCall(id="mock-id", name="get_analytics_summary", args={})
    resp1 = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[types.Part(function_call=fc)],
                    role="model"
                )
            )
        ]
    )
    resp2 = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[types.Part.from_text(text="Here is your analytics summary.")],
                    role="model"
                )
            )
        ]
    )

    mock_client.models.generate_content.side_effect = [resp1, resp2]

    service = GeminiCopilotService(mock_config)
    final_text = service.process_message("Give me summary")

    assert final_text == "Here is your analytics summary."
    assert mock_client.models.generate_content.call_count == 2

    # Verify the second call contained the tool response
    second_call_args = mock_client.models.generate_content.call_args_list[1]
    contents = second_call_args.kwargs['contents']
    assert len(contents) == 3 # user, model (function call), tool (function response)

    assert contents[0].role == "user"
    assert contents[1].role == "model"
    assert contents[1].parts[0].function_call.name == "get_analytics_summary"
    assert contents[2].role == "user"
    assert contents[2].parts[0].function_response.name == "get_analytics_summary"

@patch("backend.app.copilot.service.get_client")
def test_service_executor_error_propagation(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Setup mock to call unknown tool which will fail executor
    fc = types.FunctionCall(id="mock-id", name="invalid_tool", args={})
    resp1 = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[types.Part(function_call=fc)],
                    role="model"
                )
            )
        ]
    )
    resp2 = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    parts=[types.Part.from_text(text="I couldn't run that tool.")],
                    role="model"
                )
            )
        ]
    )

    mock_client.models.generate_content.side_effect = [resp1, resp2]

    service = GeminiCopilotService(mock_config)
    final_text = service.process_message("Run invalid tool")

    assert final_text == "I couldn't run that tool."

    # Verify the tool response was an error
    second_call_args = mock_client.models.generate_content.call_args_list[1]
    contents = second_call_args.kwargs['contents']

    # The third content block is the tool response
    tool_resp = contents[2].parts[0].function_response.response
    assert "error_message" in tool_resp or "error_category" in tool_resp

@patch("backend.app.copilot.service.get_client")
def test_service_max_rounds(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Return a function call infinitely
    fc = types.FunctionCall(id="mock-id", name="get_analytics_summary", args={})
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

    mock_client.models.generate_content.return_value = resp

    # Allow 2 rounds
    service = GeminiCopilotService(mock_config, max_rounds=2)
    final_text = service.process_message("Loop forever")

    assert "Maximum tool rounds exceeded" in final_text

    # The model was called exactly twice (the max rounds)
    assert mock_client.models.generate_content.call_count == 2

@patch("backend.app.copilot.service.get_client")
def test_service_provider_configuration(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Check that GeminiCopilotService correctly initializes with Vertex AI mode if configured
    config = GeminiConfig(
        gemini_model="gemini-3.1-pro",
        provider_mode=GeminiProviderMode.VERTEX_AI,
        google_cloud_project="test-project",
        google_cloud_location="us-central1"
    )

    service = GeminiCopilotService(config)
    assert service.config.provider_mode == GeminiProviderMode.VERTEX_AI

    # Verify get_client was called with this config
    mock_get_client.assert_called_once_with(config)

@patch("backend.app.copilot.service.get_client")
def test_service_malformed_response_handling(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # GenerateContentResponse with no candidates
    resp = types.GenerateContentResponse(candidates=[])

    mock_client.models.generate_content.return_value = resp

    service = GeminiCopilotService(mock_config)
    final_text = service.process_message("Hello")

    # CopilotOrchestrator exits loop if no function calls. It expects a text response.
    # If no text, the service returns the fallback string.
    assert final_text == "No text response generated."
