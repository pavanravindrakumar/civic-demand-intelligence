import logging
from typing import List, Optional
from google.genai import types

from backend.app.copilot.gemini_client import (
    GeminiConfig,
    get_client,
    get_generate_content_config
)
from backend.app.copilot.orchestrator import (
    ModelAdapter,
    ModelResponse,
    ConversationTurn,
    CopilotOrchestrator
)
from backend.app.copilot.gemini_sdk_adapter import (
    parse_sdk_response,
    build_model_content,
    build_tool_content
)
from backend.app.copilot.gemini_tools import get_gemini_tool

logger = logging.getLogger(__name__)

class GeminiModelAdapter(ModelAdapter):
    """
    Production ModelAdapter implementation bridging CopilotOrchestrator
    with the real Gemini API using Google Gen AI SDK.
    """
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.client = get_client(config)
        self.tool = get_gemini_tool()

    def _convert_history_to_contents(self, history: List[ConversationTurn]) -> List[types.Content]:
        contents: List[types.Content] = []

        for turn in history:
            if turn.role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=str(turn.content))]
                ))
            elif turn.role == "model":
                contents.append(build_model_content(turn.content))
            elif turn.role == "tool":
                contents.append(build_tool_content(turn.content))
            elif turn.role == "system":
                # Inject system messages as user messages to provide context inline
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"[System]: {turn.content}")]
                ))
        return contents

    def generate_response(self, history: List[ConversationTurn]) -> ModelResponse:
        contents = self._convert_history_to_contents(history)

        # Determine if we should allow tool calling for this turn
        # If the last turn was a tool, we set mode to NONE or ANY depending on loop logic.
        # But generally, CopilotOrchestrator loops as long as tools are called.
        # However, to prevent a second tool call right after a tool result (as verified in 7.1C.3B),
        # we might restrict it. For a general service, AUTO is typically best unless we specifically
        # want to enforce one-tool-call bounds. Let's use get_generate_content_config which has mode=AUTO.

        gen_config = get_generate_content_config()

        # If the last turn was a tool, sometimes we enforce NONE to prevent loops, but standard
        # multi-turn allows AUTO. Let's use the verified AUTO mode from gemini_client.
        # Wait, in the verified 7.1C.3B script, we used mode='NONE' for the second turn
        # to ensure it answers instead of calling again.
        # But CopilotOrchestrator handles bounds via `max_rounds`.
        # So we can safely use AUTO. If it loops, orchestrator kills it.

        try:
            response = self.client.models.generate_content(
                model=self.config.gemini_model,
                contents=contents,
                config=gen_config
            )
            return parse_sdk_response(response)
        except Exception as e:
            logger.error("Gemini API Error", extra={"safe_context": {"error_type": type(e).__name__, "operation": "copilot"}})
            # Return a graceful text error so the orchestrator can continue or exit
            # Do NOT expose raw exception details, API keys, or provider internals to the client.
            return ModelResponse(text="The AI provider is currently unavailable. Please try again later.")


class GeminiCopilotService:
    """
    Reusable application-layer service for interacting with the Copilot.
    """
    def __init__(self, config: GeminiConfig, max_rounds: int = 3):
        self.config = config
        self.adapter = GeminiModelAdapter(config)
        self.orchestrator = CopilotOrchestrator(model_adapter=self.adapter, max_rounds=max_rounds)

    def process_message(self, user_message: str) -> str:
        """
        Processes a user message through the Copilot function-calling loop.
        Returns the final AI text response.
        """
        history = self.orchestrator.orchestrate(user_message)

        # The orchestrator returns the full history. The last turn is ideally the model's text response.
        # Or it might be a system error if max bounds exceeded.

        last_turn = history[-1]

        if last_turn.role == "model" and last_turn.content.text:
            return last_turn.content.text

        if last_turn.role == "system":
            logger.warning("Copilot Safety Event", extra={"safe_context": {"operation": "copilot", "reason": str(last_turn.content)}})
            return str(last_turn.content)

        return "No text response generated."
