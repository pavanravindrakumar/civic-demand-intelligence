import pytest
from backend.app.copilot.executor import CopilotExecutor
from backend.app.copilot.tools import ToolErrorCategory
from backend.app.analytics.engine import ReadinessState

def test_valid_get_analytics_summary():
    result = CopilotExecutor.execute("get_analytics_summary", {})
    assert result.status == "SUCCESS"
    assert result.data is not None
    assert result.data.total_villages_analyzed > 0
    assert result.data.readiness_state == ReadinessState.PUBLIC_EVIDENCE_ONLY

def test_valid_get_village_analytics():
    # 586842 is a known valid code
    result = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "586842"})
    assert result.status == "SUCCESS"
    assert result.data is not None
    assert result.data.lgd_village_code == "586842"
    assert result.data.readiness == ReadinessState.PUBLIC_EVIDENCE_ONLY

def test_valid_get_analytics_readiness():
    result = CopilotExecutor.execute("get_analytics_readiness", {})
    assert result.status == "SUCCESS"
    assert result.data is not None
    assert result.data.readiness_state == "PUBLIC_EVIDENCE_ONLY"
    assert "validated_citizen_demand_count" in result.data.missing_inputs

def test_unknown_tool_name():
    result = CopilotExecutor.execute("delete_database", {})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.TOOL_NOT_ALLOWED

def test_malformed_lgd_village_code():
    result = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "123"})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.INVALID_ARGUMENT

def test_missing_argument():
    result = CopilotExecutor.execute("get_village_analytics", {})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.INVALID_ARGUMENT

def test_extra_unexpected_argument():
    result = CopilotExecutor.execute("get_analytics_summary", {"extra": "argument"})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.INVALID_ARGUMENT

def test_deterministic_repeated_execution():
    result1 = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "586842"})
    result2 = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "586842"})

    assert result1.status == "SUCCESS"
    assert result2.status == "SUCCESS"
    assert result1.data.model_dump() == result2.data.model_dump()

def test_output_model_validation():
    # Testing that the output is actually typed correctly
    result = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "586842"})
    assert result.status == "SUCCESS"
    assert type(result.data).__name__ == "PriorityResult"

def test_provenance_preservation():
    result = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "586842"})
    assert result.status == "SUCCESS"
    assert result.provenance_source == "JJM/LGD Analytics Dataset"

    summary = CopilotExecutor.execute("get_analytics_summary", {})
    assert summary.status == "SUCCESS"
    assert summary.provenance_source == "JJM/LGD Analytics Dataset"

def test_public_evidence_only_preservation():
    result = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "586842"})
    assert result.data.readiness == ReadinessState.PUBLIC_EVIDENCE_ONLY

    summary = CopilotExecutor.execute("get_analytics_summary", {})
    assert summary.data.readiness_state == ReadinessState.PUBLIC_EVIDENCE_ONLY

def test_attempt_to_pass_sql_text():
    result = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "DROP TABLE villages;"})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.INVALID_ARGUMENT

def test_attempt_to_pass_filesystem_path():
    result = CopilotExecutor.execute("get_village_analytics", {"lgd_village_code": "../../../etc/passwd"})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.INVALID_ARGUMENT

def test_attempt_to_invoke_write_capable_unknown_tool():
    result = CopilotExecutor.execute("update_village_data", {"lgd_village_code": "271011", "gap": 0})
    assert result.status == "ERROR"
    assert result.error_category == ToolErrorCategory.TOOL_NOT_ALLOWED
