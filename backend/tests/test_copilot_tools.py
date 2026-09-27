import pytest
from pydantic import BaseModel
from backend.app.copilot.tools import (
    CopilotToolRegistry, ToolDefinition, ToolAuthorization, ToolErrorCategory,
    GetAnalyticsSummaryInput, GetVillageAnalyticsInput, GetAnalyticsReadinessInput,
    AnalyticsSummary, PriorityResult, ReadinessOutput
)

def dummy_summary_handler(inputs: GetAnalyticsSummaryInput):
    return AnalyticsSummary(
        total_villages_analyzed=1,
        total_households=10,
        total_fhtc=5,
        total_reported_household_gap=5,
        readiness_state="PUBLIC_EVIDENCE_ONLY",
        calculation_version="v1.0"
    )

def dummy_village_handler(inputs: GetVillageAnalyticsInput):
    if inputs.lgd_village_code == "999999":
        raise ValueError("Village not found")

    # Needs to match the PriorityResult model loosely for the test
    return {
        "lgd_village_code": inputs.lgd_village_code,
        "readiness": "PUBLIC_EVIDENCE_ONLY",
        "evidence_quality": "PARTIAL",
        "calculation_version": "v1.0",
        "normalized_gap": 0.5,
        "normalized_exposure": 0.1,
        "normalized_demand": 0.0,
        "reported_household_gap": 50,
        "household_exposure": 100,
        "priority_score": None
    }

@pytest.fixture
def registry():
    reg = CopilotToolRegistry()
    reg.register(ToolDefinition(
        name="get_analytics_summary",
        description="Get global summary",
        input_schema=GetAnalyticsSummaryInput,
        output_schema=AnalyticsSummary,
        handler=dummy_summary_handler
    ))
    reg.register(ToolDefinition(
        name="get_village_analytics",
        description="Get village analytics",
        input_schema=GetVillageAnalyticsInput,
        output_schema=PriorityResult,
        handler=dummy_village_handler
    ))
    return reg

def test_registry_approved_tools(registry):
    assert registry.get_tool("get_analytics_summary") is not None
    assert registry.get_tool("get_village_analytics") is not None

def test_unknown_tool_rejected(registry):
    result = registry.execute_tool("hack_database", {})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.TOOL_NOT_ALLOWED

def test_malformed_lgd_village_code_rejected(registry):
    # LGD code must be exactly 6 digits according to regex `^\d{6}$`
    result1 = registry.execute_tool("get_village_analytics", {"lgd_village_code": "123"})
    assert result1.status == "ERROR"
    assert result1.error_category == ToolErrorCategory.INVALID_ARGUMENT

    result2 = registry.execute_tool("get_village_analytics", {"lgd_village_code": "DROP TABLE villages;"})
    assert result2.status == "ERROR"
    assert result2.error_category == ToolErrorCategory.INVALID_ARGUMENT

def test_valid_village_lookup(registry):
    result = registry.execute_tool("get_village_analytics", {"lgd_village_code": "271011"})
    assert result.status == "SUCCESS"
    assert result.data.lgd_village_code == "271011"
    assert result.provenance_source == "JJM/LGD Analytics Dataset"

def test_village_not_found(registry):
    result = registry.execute_tool("get_village_analytics", {"lgd_village_code": "999999"})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.NOT_FOUND

def test_write_capable_tool_rejected():
    reg = CopilotToolRegistry()

    class DummyInput(BaseModel): pass
    class DummyOutput(BaseModel): pass

    with pytest.raises(Exception, match="READ_ONLY"):
        reg.register(ToolDefinition(
            name="mutate_data",
            description="Mutate data",
            input_schema=DummyInput,
            output_schema=DummyOutput,
            authorization="WRITE_CAPABLE", # Invalid for this phase
            handler=lambda x: None
        ))
