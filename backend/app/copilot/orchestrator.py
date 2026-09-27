import json
from typing import List, Dict, Any, Optional, Protocol, Set
from pydantic import BaseModel

from backend.app.copilot.executor import CopilotExecutor

class FunctionCallRequest(BaseModel):
    id: str
    name: str
    args: Dict[str, Any]

class ModelResponse(BaseModel):
    text: Optional[str] = None
    function_calls: List[FunctionCallRequest] = []
    raw_content: Any = None  # To preserve exact SDK Content (e.g. thought_signature)

class FunctionCallResponse(BaseModel):
    id: str
    name: str
    result: Any
    is_error: bool = False

class ConversationTurn(BaseModel):
    role: str  # "user", "model", "tool", "system"
    content: Any # str, ModelResponse, or List[FunctionCallResponse]

class ModelAdapter(Protocol):
    """
    Interface for the model adapter.
    In real implementations, this translates our conversational state to Google GenAI SDK.
    In tests, this is a mock.
    """
    def generate_response(self, history: List[ConversationTurn]) -> ModelResponse:
        ...

class CopilotOrchestrator:
    """
    Application-level orchestration loop for the Copilot.
    """
    def __init__(self, model_adapter: ModelAdapter, max_rounds: int = 3):
        self.model_adapter = model_adapter
        self.max_rounds = max_rounds

    def orchestrate(self, user_text: str) -> List[ConversationTurn]:
        history = [ConversationTurn(role="user", content=user_text)]

        rounds = 0
        executed_calls: Set[str] = set()

        while rounds < self.max_rounds:
            rounds += 1

            # 1. Ask the model for the next step
            model_resp = self.model_adapter.generate_response(history)
            history.append(ConversationTurn(role="model", content=model_resp))

            # 2. If the model didn't call any functions, the turn is over
            if not model_resp.function_calls:
                return history

            # 3. Handle function calls deterministically and sequentially
            tool_responses: List[FunctionCallResponse] = []

            for fcall in model_resp.function_calls:
                # Repeated call protection (to prevent infinite loops if model breaks)
                # Serialize args safely for hashing
                call_signature = f"{fcall.name}:{json.dumps(fcall.args, sort_keys=True)}"
                if call_signature in executed_calls:
                    tool_responses.append(FunctionCallResponse(
                        id=fcall.id,
                        name=fcall.name,
                        result={"error": "Repeated tool call prevented by loop protection."},
                        is_error=True
                    ))
                    continue

                executed_calls.add(call_signature)

                # Execute strictly through CopilotExecutor! No arbitrary callables.
                result_wrapper = CopilotExecutor.execute(fcall.name, fcall.args)

                is_error = result_wrapper.status == "ERROR"
                if is_error:
                    # Return safe, structured error
                    result_payload = {
                        "error_category": result_wrapper.error_category.value if result_wrapper.error_category else "INTERNAL_ERROR",
                        "error_message": result_wrapper.error_message
                    }
                else:
                    # Return structured data, preserving readiness and provenance
                    result_payload = result_wrapper.model_dump()

                tool_responses.append(FunctionCallResponse(
                    id=fcall.id,
                    name=fcall.name,
                    result=result_payload,
                    is_error=is_error
                ))

            # 4. Give the tool results back to the model history and continue loop
            history.append(ConversationTurn(role="tool", content=tool_responses))

        # If we exit the loop because of max rounds
        history.append(ConversationTurn(
            role="system",
            content="Error: Maximum tool rounds exceeded. Safety limit triggered."
        ))

        return history
