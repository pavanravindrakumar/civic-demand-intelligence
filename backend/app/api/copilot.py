from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from backend.app.copilot.service import GeminiCopilotService
from backend.app.api.middleware import copilot_limiter


router = APIRouter(prefix="/api/copilot", tags=["copilot"])

class CopilotChatRequest(BaseModel):
    message: str = Field(..., max_length=1000, description="The user's message to the copilot.")

class ToolCallMetadata(BaseModel):
    name: str
    args: dict

class ProvenanceMetadata(BaseModel):
    source_dataset: Optional[str] = None
    calculation_version: Optional[str] = None

class CopilotMetadata(BaseModel):
    tool_calls: List[ToolCallMetadata] = []
    provenance: List[ProvenanceMetadata] = []

class CopilotChatResponse(BaseModel):
    text: str
    status: str
    error_message: Optional[str] = None
    metadata: CopilotMetadata

import os
from backend.app.copilot.gemini_client import GeminiConfig, GeminiProviderMode

def get_copilot_service() -> GeminiCopilotService:
    # Use environment variables
    model_id = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')
    api_key = os.getenv('GEMINI_API_KEY')
    provider = os.getenv('GEMINI_PROVIDER_MODE', 'developer_api')

    config = GeminiConfig(
        gemini_model=model_id,
        provider_mode=GeminiProviderMode(provider),
        api_key=api_key,
        google_cloud_project=os.getenv('GOOGLE_CLOUD_PROJECT'),
        google_cloud_location=os.getenv('GOOGLE_CLOUD_LOCATION')
    )
    return GeminiCopilotService(config=config)

@router.post("/chat", response_model=CopilotChatResponse, dependencies=[Depends(copilot_limiter)])
def copilot_chat(request: CopilotChatRequest, service: GeminiCopilotService = Depends(get_copilot_service)):
    """
    Submit a message to the Gemini Copilot.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # Instead of just process_message (which returns str), we can get the history from orchestrate
        # to construct the rich metadata.
        history = service.orchestrator.orchestrate(request.message)

        last_turn = history[-1]
        text_response = "No text response generated."
        status = "success"

        if last_turn.role == "model" and last_turn.content.text:
            text_response = last_turn.content.text
        elif last_turn.role == "system":
            text_response = str(last_turn.content)
            status = "error"

        # Extract metadata from history
        tool_calls = []
        provenances = []

        for turn in history:
            if turn.role == "model" and hasattr(turn.content, "function_calls") and turn.content.function_calls:
                for fc in turn.content.function_calls:
                    tool_calls.append(ToolCallMetadata(name=fc.name, args=fc.args))
            elif turn.role == "tool" and isinstance(turn.content, list):
                for fr in turn.content:
                    if isinstance(fr.result, dict):
                        prov = fr.result.get("provenance")
                        if prov:
                            provenances.append(ProvenanceMetadata(
                                source_dataset=prov.get("source_dataset"),
                                calculation_version=prov.get("calculation_version")
                            ))

        return CopilotChatResponse(
            text=text_response,
            status=status,
            metadata=CopilotMetadata(
                tool_calls=tool_calls,
                provenance=provenances
            )
        )
    except Exception as e:
        # Prevent leaking stack traces to the client
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the request.")
