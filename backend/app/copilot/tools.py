from enum import Enum
from pydantic import BaseModel, Field, constr
from typing import Dict, Any, Type, Callable
from backend.app.data.analytics_repository import AnalyticsSummary
from backend.app.analytics.engine import PriorityResult

class ToolErrorCategory(str, Enum):
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    TOOL_NOT_ALLOWED = "TOOL_NOT_ALLOWED"
    NOT_FOUND = "NOT_FOUND"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    INCOMPLETE_INPUTS = "INCOMPLETE_INPUTS"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class ToolAuthorization(str, Enum):
    READ_ONLY = "READ_ONLY"

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    authorization: ToolAuthorization = ToolAuthorization.READ_ONLY
    handler: Callable[[Any], Any]

# --- Input Schemas ---

class GetAnalyticsSummaryInput(BaseModel):
    model_config = {"extra": "forbid"}

class GetVillageAnalyticsInput(BaseModel):
    model_config = {"extra": "forbid"}
    lgd_village_code: str = Field(
        ...,
        description="The canonical LGD Village Code (exactly 6 digits).",
        pattern=r"^\d{6}$"
    )

class GetAnalyticsReadinessInput(BaseModel):
    model_config = {"extra": "forbid"}

# --- Output Schemas ---
# We reuse the actual Pydantic models from analytics where possible,
# or wrap them to add explicit provenance tracing.

class CopilotResultWrapper(BaseModel):
    tool_name: str
    status: str = "SUCCESS"
    data: Any
    provenance_source: str = "JJM/LGD Analytics Dataset"
    error_category: ToolErrorCategory | None = None
    error_message: str | None = None

class ReadinessOutput(BaseModel):
    readiness_state: str
    missing_inputs: list[str]

# --- Registry ---

class CopilotToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool_def: ToolDefinition):
        if tool_def.authorization != ToolAuthorization.READ_ONLY:
            raise ValueError("Only READ_ONLY tools are allowed in this phase.")
        self._tools[tool_def.name] = tool_def

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def execute_tool(self, name: str, kwargs: dict) -> CopilotResultWrapper:
        tool = self.get_tool(name)
        if not tool:
            return CopilotResultWrapper(
                tool_name=name,
                status="ERROR",
                data=None,
                error_category=ToolErrorCategory.TOOL_NOT_ALLOWED,
                error_message=f"Tool '{name}' is not registered or not allowed."
            )

        try:
            # Strictly parse and validate inputs
            validated_inputs = tool.input_schema(**kwargs)
        except Exception as e:
            return CopilotResultWrapper(
                tool_name=name,
                status="ERROR",
                data=None,
                error_category=ToolErrorCategory.INVALID_ARGUMENT,
                error_message=f"Input validation failed: {str(e)}"
            )

        try:
            # Execute underlying deterministic handler
            result = tool.handler(validated_inputs)

            # Optionally validate output schema if the handler doesn't return the exact type
            if not isinstance(result, tool.output_schema):
                result = tool.output_schema.model_validate(result)

            return CopilotResultWrapper(
                tool_name=name,
                data=result
            )
        except ValueError as e:
            # E.g. Not Found
            return CopilotResultWrapper(
                tool_name=name,
                status="ERROR",
                data=None,
                error_category=ToolErrorCategory.NOT_FOUND,
                error_message=str(e)
            )
        except Exception as e:
            return CopilotResultWrapper(
                tool_name=name,
                status="ERROR",
                data=None,
                error_category=ToolErrorCategory.INTERNAL_ERROR,
                error_message="An internal error occurred during tool execution."
            )
