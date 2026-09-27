from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from google.genai import Client, types

from backend.app.copilot.gemini_tools import get_gemini_tool
from backend.app.copilot.orchestrator import FunctionCallRequest, FunctionCallResponse

class GeminiProviderMode(str, Enum):
    DEVELOPER_API = "developer_api"
    VERTEX_AI = "vertex_ai"

class GeminiConfig(BaseModel):
    """
    Configuration for Gemini client.
    Supports both Google Cloud Vertex AI (ADC) and Gemini Developer API (API Key).
    """
    gemini_model: str = Field(..., min_length=1, description="Model identifier (e.g. gemini-3.1-flash-lite)")
    provider_mode: GeminiProviderMode = Field(default=GeminiProviderMode.DEVELOPER_API)

    # Vertex AI requirements
    google_cloud_project: Optional[str] = Field(default=None, description="GCP Project ID")
    google_cloud_location: Optional[str] = Field(default=None, description="GCP Location")

    # Developer API requirements
    api_key: Optional[str] = Field(default=None, description="Gemini API Key", exclude=True)

    @model_validator(mode='after')
    def validate_provider_requirements(self) -> "GeminiConfig":
        if self.provider_mode == GeminiProviderMode.VERTEX_AI:
            if not self.google_cloud_project or not self.google_cloud_location:
                raise ValueError("google_cloud_project and google_cloud_location are required when using vertex_ai mode.")
            if self.api_key is not None:
                raise ValueError("API Key must not be configured when using Google Cloud (Vertex AI) ADC mode.")
        elif self.provider_mode == GeminiProviderMode.DEVELOPER_API:
            if not self.api_key:
                raise ValueError("api_key is required when using developer_api mode.")
        return self

def get_client(config: GeminiConfig) -> Client:
    """
    Constructs the google-genai Client depending on the provider mode.
    Does NOT invoke the network upon construction.
    """
    if config.provider_mode == GeminiProviderMode.VERTEX_AI:
        return Client(
            vertexai=True,
            project=config.google_cloud_project,
            location=config.google_cloud_location
        )
    else:
        return Client(api_key=config.api_key)

def get_generate_content_config() -> types.GenerateContentConfig:
    """
    Helper to configure manual function calling with the approved Copilot registry.
    """
    tool = get_gemini_tool()

    system_instruction = (
        "Use approved tools for authoritative analytics. Do not invent statistics. "
        "Do not invent evidence. Do not fabricate citizen demand. "
        "Cite/use tool-returned provenance. Distinguish measured data from explanation. "
        "Respect PUBLIC_EVIDENCE_ONLY. Do not claim unsupported population values. "
        "Do not reinterpret reported household gap."
    )

    return types.GenerateContentConfig(
        tools=[tool],
        system_instruction=system_instruction,
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="AUTO"
            )
        )
    )

def convert_to_orchestrator_call(fc: types.FunctionCall) -> FunctionCallRequest:
    """
    Adapter converting SDK FunctionCall to application-owned FunctionCallRequest.
    """
    return FunctionCallRequest(
        id=fc.id or "",
        name=fc.name,
        args=fc.args or {}
    )

def convert_to_sdk_response(fcr: FunctionCallResponse) -> types.Part:
    """
    Adapter converting application-owned deterministic tool result into SDK Part.
    """
    # The payload is naturally JSON-serializable structured data
    fr = types.FunctionResponse(
        id=fcr.id,
        name=fcr.name,
        response=fcr.result
    )
    return types.Part(function_response=fr)
