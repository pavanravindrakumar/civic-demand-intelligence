import pytest
from typing import List
from backend.app.copilot.orchestrator import (
    CopilotOrchestrator,
    ModelAdapter,
    ModelResponse,
    FunctionCallRequest,
    ConversationTurn
)

class MockModelAdapter(ModelAdapter):
    def __init__(self, scripted_responses: List[ModelResponse]):
        self.scripted_responses = scripted_responses
        self.turn_index = 0

    def generate_response(self, history: List[ConversationTurn]) -> ModelResponse:
        if self.turn_index < len(self.scripted_responses):
            resp = self.scripted_responses[self.turn_index]
            self.turn_index += 1
            return resp
        # Default fallback text if we run out of scripted responses
        return ModelResponse(text="Fallback final text.")

def test_text_only_response():
    mock = MockModelAdapter([ModelResponse(text="Hello, I am a copilot.")])
    orchestrator = CopilotOrchestrator(mock)

    history = orchestrator.orchestrate("Hi")

    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "model"
    assert history[1].content.text == "Hello, I am a copilot."
    assert not history[1].content.function_calls

def test_single_summary_tool_call():
    mock = MockModelAdapter([
        ModelResponse(function_calls=[FunctionCallRequest(id="call_1", name="get_analytics_summary", args={})]),
        ModelResponse(text="The gap is large.")
    ])
    orchestrator = CopilotOrchestrator(mock)

    history = orchestrator.orchestrate("What is the summary?")

    assert len(history) == 4
    assert history[2].role == "tool"
    assert len(history[2].content) == 1
    tool_resp = history[2].content[0]
    assert tool_resp.name == "get_analytics_summary"
    assert not tool_resp.is_error
    assert tool_resp.result["status"] == "SUCCESS"

    # Check provenance
    assert tool_resp.result["provenance_source"] == "JJM/LGD Analytics Dataset"

    assert history[3].role == "model"
    assert history[3].content.text == "The gap is large."

def test_single_village_tool_call():
    mock = MockModelAdapter([
        ModelResponse(function_calls=[FunctionCallRequest(id="call_1", name="get_village_analytics", args={"lgd_village_code": "586842"})]),
        ModelResponse(text="Here is the village info.")
    ])
    orchestrator = CopilotOrchestrator(mock)

    history = orchestrator.orchestrate("Tell me about 586842")

    assert len(history) == 4
    tool_resp = history[2].content[0]
    assert tool_resp.name == "get_village_analytics"
    assert not tool_resp.is_error

    # Check PUBLIC_EVIDENCE_ONLY preservation
    assert tool_resp.result["data"]["readiness"] == "PUBLIC_EVIDENCE_ONLY"
    assert tool_resp.result["provenance_source"] == "JJM/LGD Analytics Dataset"

def test_readiness_tool_call():
    mock = MockModelAdapter([
        ModelResponse(function_calls=[FunctionCallRequest(id="call_1", name="get_analytics_readiness", args={})]),
        ModelResponse(text="Readiness is public only.")
    ])
    orchestrator = CopilotOrchestrator(mock)
    history = orchestrator.orchestrate("Readiness?")

    tool_resp = history[2].content[0]
    assert tool_resp.name == "get_analytics_readiness"
    assert tool_resp.result["data"]["readiness_state"] == "PUBLIC_EVIDENCE_ONLY"

def test_multiple_tool_calls():
    mock = MockModelAdapter([
        ModelResponse(function_calls=[
            FunctionCallRequest(id="call_1", name="get_analytics_summary", args={}),
            FunctionCallRequest(id="call_2", name="get_analytics_readiness", args={})
        ]),
        ModelResponse(text="Done multiple.")
    ])
    orchestrator = CopilotOrchestrator(mock)
    history = orchestrator.orchestrate("Do multiple")

    tool_turn = history[2]
    assert len(tool_turn.content) == 2
    assert tool_turn.content[0].name == "get_analytics_summary"
    assert tool_turn.content[1].name == "get_analytics_readiness"

def test_unknown_tool():
    mock = MockModelAdapter([
        ModelResponse(function_calls=[FunctionCallRequest(id="call_1", name="hack_database", args={})]),
        ModelResponse(text="Oops")
    ])
    orchestrator = CopilotOrchestrator(mock)
    history = orchestrator.orchestrate("Hack it")

    tool_resp = history[2].content[0]
    assert tool_resp.name == "hack_database"
    assert tool_resp.is_error
    assert tool_resp.result["error_category"] == "TOOL_NOT_ALLOWED"

def test_malformed_arguments():
    mock = MockModelAdapter([
        ModelResponse(function_calls=[FunctionCallRequest(id="call_1", name="get_village_analytics", args={"lgd_village_code": "123"})]), # invalid regex (must be 6 digits)
        ModelResponse(text="Oops")
    ])
    orchestrator = CopilotOrchestrator(mock)
    history = orchestrator.orchestrate("Village 123")

    tool_resp = history[2].content[0]
    assert tool_resp.is_error
    assert tool_resp.result["error_category"] == "INVALID_ARGUMENT"

def test_tool_error_followed_by_final_text():
    mock = MockModelAdapter([
        ModelResponse(function_calls=[FunctionCallRequest(id="call_1", name="get_village_analytics", args={"lgd_village_code": "999999"})]), # Not found
        ModelResponse(text="I couldn't find that village.")
    ])
    orchestrator = CopilotOrchestrator(mock)
    history = orchestrator.orchestrate("Village 999999")

    tool_resp = history[2].content[0]
    assert tool_resp.is_error
    assert tool_resp.result["error_category"] == "NOT_FOUND"

    assert history[3].role == "model"
    assert history[3].content.text == "I couldn't find that village."

def test_maximum_tool_round_enforcement():
    # Model keeps asking for the same tool but with slightly different args to avoid repeat protection
    mock = MockModelAdapter([
        ModelResponse(function_calls=[FunctionCallRequest(id="call_1", name="get_analytics_summary", args={"foo": 1})]),
        ModelResponse(function_calls=[FunctionCallRequest(id="call_2", name="get_analytics_summary", args={"foo": 2})]),
        ModelResponse(function_calls=[FunctionCallRequest(id="call_3", name="get_analytics_summary", args={"foo": 3})]),
        ModelResponse(function_calls=[FunctionCallRequest(id="call_4", name="get_analytics_summary", args={"foo": 4})])
    ])
    orchestrator = CopilotOrchestrator(mock, max_rounds=2)
    history = orchestrator.orchestrate("Go infinite")

    assert history[-1].role == "system"
    assert "Maximum tool rounds exceeded" in history[-1].content

def test_repeated_call_protection():
    # Model requests exactly the same tool and args twice in a row
    mock = MockModelAdapter([
        ModelResponse(function_calls=[FunctionCallRequest(id="call_1", name="get_analytics_summary", args={})]),
        ModelResponse(function_calls=[FunctionCallRequest(id="call_2", name="get_analytics_summary", args={})]),
        ModelResponse(text="Okay done")
    ])
    orchestrator = CopilotOrchestrator(mock)
    history = orchestrator.orchestrate("Do it")

    # First turn: model asks for summary
    # Second turn: tool returns success
    # Third turn: model asks for summary AGAIN
    # Fourth turn: tool returns error for repeated call
    tool_resp_1 = history[2].content[0]
    assert not tool_resp_1.is_error

    tool_resp_2 = history[4].content[0]
    assert tool_resp_2.is_error
    assert "Repeated tool call prevented" in tool_resp_2.result["error"]

    assert history[5].role == "model"
    assert history[5].content.text == "Okay done"
