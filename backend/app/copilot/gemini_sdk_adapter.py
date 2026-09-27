from typing import List, Optional
from google.genai import types

from backend.app.copilot.orchestrator import (
    ModelResponse,
    FunctionCallRequest,
    FunctionCallResponse,
    ConversationTurn
)
from backend.app.copilot.gemini_client import (
    convert_to_orchestrator_call,
    convert_to_sdk_response
)

def parse_sdk_response(response: types.GenerateContentResponse) -> ModelResponse:
    """
    Parses a real Google Gen AI SDK response into the internal Copilot ModelResponse.
    Supports text-only, single function call, multiple function calls, and malformed/empty responses.
    """
    model_response = ModelResponse()

    # Preserve the exact SDK Content (e.g. for thought_signatures) if candidates exist
    if response.candidates and response.candidates[0].content:
        model_response.raw_content = response.candidates[0].content

    if response.text:
        model_response.text = response.text

    if response.function_calls:
        for fc in response.function_calls:
            model_response.function_calls.append(convert_to_orchestrator_call(fc))

    return model_response

def build_model_content(model_resp: ModelResponse) -> types.Content:
    """
    Constructs the model's original turn Content for the history.
    If raw_content is available, it returns it exactly to preserve thought_signatures.
    Otherwise it reconstructs it from the function_calls.
    """
    if model_resp.raw_content is not None:
        return model_resp.raw_content
    parts = []
    if model_resp.text:
        parts.append(types.Part.from_text(text=model_resp.text))

    if model_resp.function_calls:
        for fcr in model_resp.function_calls:
            fc = types.FunctionCall(
                id=fcr.id,
                name=fcr.name,
                args=fcr.args
            )
            parts.append(types.Part(function_call=fc))

    return types.Content(role="model", parts=parts)

def build_tool_content(tool_responses: List[FunctionCallResponse]) -> types.Content:
    """
    Constructs the tool's response Content for the history, containing all FunctionResponses.
    """
    parts = []
    for fcr in tool_responses:
        parts.append(convert_to_sdk_response(fcr))

    return types.Content(role="user", parts=parts)  # The SDK expects tool responses in a user role or a user/tool structure. Wait, google.genai expects tool responses in role="user" or role="tool"? Actually google.genai expects role="user" or role="tool", let's use "user" for tool response per Vertex typical mapping, or "tool" if google-genai supports it. Usually role="user" is used for tool responses in some SDK versions, but google.genai types.Content(role="user", parts=[types.Part.from_function_response(...)]) is standard.
