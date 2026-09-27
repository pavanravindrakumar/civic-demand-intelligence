from typing import Any, Dict
from pydantic import ValidationError

from backend.app.copilot.tools import (
    CopilotToolRegistry,
    ToolDefinition,
    ToolErrorCategory,
    GetAnalyticsSummaryInput,
    GetVillageAnalyticsInput,
    GetAnalyticsReadinessInput,
    ReadinessOutput,
    CopilotResultWrapper
)
from backend.app.data.analytics_repository import AnalyticsRepository, AnalyticsSummary
from backend.app.analytics.engine import PriorityResult

# Instantiate a single repository for the executor (caching loaded data)
_repo = AnalyticsRepository()

# Instantiate and configure the registry (Allowlist)
registry = CopilotToolRegistry()

def _handle_summary(inputs: GetAnalyticsSummaryInput) -> AnalyticsSummary:
    return _repo.get_summary()

def _handle_village(inputs: GetVillageAnalyticsInput) -> PriorityResult:
    res = _repo.get_village_analytics(inputs.lgd_village_code)
    if not res:
        raise ValueError(f"Village with LGD code {inputs.lgd_village_code} not found.")
    return res

def _handle_readiness(inputs: GetAnalyticsReadinessInput) -> ReadinessOutput:
    summary = _repo.get_summary()
    return ReadinessOutput(
        readiness_state=summary.readiness_state.value,
        missing_inputs=["validated_citizen_demand_count"]
    )

# Strict Explicit Allowlist Registration
registry.register(ToolDefinition(
    name="get_analytics_summary",
    description="Get deterministic global analytics summary.",
    input_schema=GetAnalyticsSummaryInput,
    output_schema=AnalyticsSummary,
    handler=_handle_summary
))

registry.register(ToolDefinition(
    name="get_village_analytics",
    description="Get deterministic analytics for a specific village.",
    input_schema=GetVillageAnalyticsInput,
    output_schema=PriorityResult,
    handler=_handle_village
))

registry.register(ToolDefinition(
    name="get_analytics_readiness",
    description="Get current readiness state of the analytics engine.",
    input_schema=GetAnalyticsReadinessInput,
    output_schema=ReadinessOutput,
    handler=_handle_readiness
))

class CopilotExecutor:
    """
    Deterministic executor for Copilot Tools.
    Absolutely no LLM/Gemini integration exists in this layer.
    """

    @staticmethod
    def execute(tool_name: str, kwargs: Dict[str, Any]) -> CopilotResultWrapper:
        """
        Execution Flow:
        1. incoming tool name -> allowlist lookup (via registry)
        2. typed input validation (via registry execution)
        3. deterministic tool execution (via registry execution)
        4. typed output validation (via registry execution)
        5. structured result/error
        """
        # The registry explicitly returns TOOL_NOT_ALLOWED for unknown tools
        # and INVALID_ARGUMENT for malformed inputs, preserving provenance.
        return registry.execute_tool(tool_name, kwargs)
