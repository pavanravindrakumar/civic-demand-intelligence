import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from backend.app.main import app
from backend.app.api.copilot import get_copilot_service
from backend.app.copilot.orchestrator import ConversationTurn, ModelResponse, FunctionCallRequest, FunctionCallResponse

client = TestClient(app)

@pytest.fixture
def mock_service():
    service = MagicMock()
    # By default, setup orchestrate to return a simple text response
    service.orchestrator.orchestrate.return_value = [
        ConversationTurn(role="user", content="Hello"),
        ConversationTurn(role="model", content=ModelResponse(text="Hi there!"))
    ]
    app.dependency_overrides[get_copilot_service] = lambda: service
    yield service
    app.dependency_overrides.clear()

def test_copilot_valid_request(mock_service):
    response = client.post("/api/copilot/chat", json={"message": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Hi there!"
    assert data["status"] == "success"
    assert "metadata" in data
    assert len(data["metadata"]["tool_calls"]) == 0
    assert len(data["metadata"]["provenance"]) == 0

def test_copilot_empty_message(mock_service):
    response = client.post("/api/copilot/chat", json={"message": "   "})
    assert response.status_code == 400
    assert "Message cannot be empty" in response.json()["detail"]

def test_copilot_invalid_contract(mock_service):
    response = client.post("/api/copilot/chat", json={}) # Missing message
    assert response.status_code == 422 # Pydantic validation error

def test_copilot_tool_backed_response(mock_service):
    # Setup orchestrate to return a conversation with a tool call and response
    fc_request = FunctionCallRequest(id="call_1", name="get_analytics_summary", args={})
    model_resp1 = ModelResponse(function_calls=[fc_request])

    fc_result = {
        "data": {"total_villages_analyzed": 10},
        "provenance": {"source_dataset": "JJM/LGD Analytics Dataset", "calculation_version": "v1.0"}
    }
    fc_resp = FunctionCallResponse(id="call_1", name="get_analytics_summary", result=fc_result)

    model_resp2 = ModelResponse(text="The total villages is 10.")

    mock_service.orchestrator.orchestrate.return_value = [
        ConversationTurn(role="user", content="Give me a summary"),
        ConversationTurn(role="model", content=model_resp1),
        ConversationTurn(role="tool", content=[fc_resp]),
        ConversationTurn(role="model", content=model_resp2)
    ]

    response = client.post("/api/copilot/chat", json={"message": "Give me a summary"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "The total villages is 10."
    assert len(data["metadata"]["tool_calls"]) == 1
    assert data["metadata"]["tool_calls"][0]["name"] == "get_analytics_summary"

    assert len(data["metadata"]["provenance"]) == 1
    assert data["metadata"]["provenance"][0]["source_dataset"] == "JJM/LGD Analytics Dataset"

def test_copilot_service_failure(mock_service):
    # If orchestrate throws an unhandled exception, FastAPI returns 500 without leaking details
    mock_service.orchestrator.orchestrate.side_effect = Exception("Secret failure stack trace")

    response = client.post("/api/copilot/chat", json={"message": "Break"})
    assert response.status_code == 500
    assert "internal error" in response.json()["detail"].lower()
    assert "Secret failure stack trace" not in response.json()["detail"]

def test_copilot_system_error_response(mock_service):
    # E.g. max tool loops reached
    mock_service.orchestrator.orchestrate.return_value = [
        ConversationTurn(role="user", content="Loop forever"),
        ConversationTurn(role="system", content="Error: Maximum tool rounds exceeded. Safety limit triggered.")
    ]

    response = client.post("/api/copilot/chat", json={"message": "Loop forever"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Maximum tool rounds exceeded" in data["text"]
