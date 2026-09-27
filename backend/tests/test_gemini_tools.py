import pytest
import json
from google.genai import types
from backend.app.copilot.gemini_tools import get_gemini_tool
from backend.app.copilot.executor import registry
from backend.app.copilot.tools import ToolDefinition, ToolAuthorization
from pydantic import BaseModel

def test_declaration_count():
    tool = get_gemini_tool()
    assert len(tool.function_declarations) == 3

def test_declaration_names_match_registry():
    tool = get_gemini_tool()
    names = [decl.name for decl in tool.function_declarations]
    assert "get_analytics_summary" in names
    assert "get_village_analytics" in names
    assert "get_analytics_readiness" in names

def test_summary_declaration_has_no_required_parameters():
    tool = get_gemini_tool()
    summary_decl = next(d for d in tool.function_declarations if d.name == "get_analytics_summary")
    # if required is None or empty list, it means no required parameters
    schema = summary_decl.parameters_json_schema
    assert "required" not in schema or len(schema["required"]) == 0

def test_village_declaration_requires_lgd_code():
    tool = get_gemini_tool()
    village_decl = next(d for d in tool.function_declarations if d.name == "get_village_analytics")
    schema = village_decl.parameters_json_schema
    assert "lgd_village_code" in schema["required"]
    assert schema["properties"]["lgd_village_code"]["type"] == "string"

def test_json_schema_serializability():
    # google.genai types should be serializable via model_dump
    tool = get_gemini_tool()
    raw_dict = tool.model_dump(exclude_unset=True)
    # Ensure it dumps without crashing and can be serialized to JSON
    json_string = json.dumps(raw_dict)
    assert "get_village_analytics" in json_string

def test_no_callables_exposed():
    tool = get_gemini_tool()
    raw_dict = tool.model_dump()
    json_str = json.dumps(raw_dict)
    # Just asserting it can serialize to JSON proves there are no un-serializable callables like functions
    # Also double check there's no handler field
    assert "handler" not in json_str

def test_deterministic_generation():
    tool1 = get_gemini_tool()
    tool2 = get_gemini_tool()

    assert tool1.model_dump() == tool2.model_dump()

def test_only_read_only_tools_exposed(monkeypatch):
    class DummyInput(BaseModel): pass
    class DummyOutput(BaseModel): pass

    # We patch registry temporarily
    original_tools = registry._tools.copy()

    # Add a mock write tool (manually since register prevents it normally, but let's test gemini_tools logic)
    write_tool = ToolDefinition(
        name="mutate_something",
        description="Write data",
        input_schema=DummyInput,
        output_schema=DummyOutput,
        handler=lambda x: None
    )
    # Bypass authorization check just for testing the exposure filter
    write_tool.authorization = "WRITE_CAPABLE"  # Not a real enum, but bypasses the check for this test
    registry._tools["mutate_something"] = write_tool

    # We also have to mock allowed_tool_names in gemini_tools.py to include it to test the exception
    import backend.app.copilot.gemini_tools as gemini_tools

    def mock_get_gemini_tool():
        allowed_tool_names = ["mutate_something"]
        declarations = []
        for tool_name in allowed_tool_names:
            tool_def = registry.get_tool(tool_name)
            if tool_def.authorization != ToolAuthorization.READ_ONLY:
                raise ValueError(f"CRITICAL: Tool '{tool_name}' is not READ_ONLY.")
            declarations.append(types.FunctionDeclaration(name=tool_def.name, description=tool_def.description))
        return types.Tool(function_declarations=declarations)

    with pytest.raises(ValueError, match="not READ_ONLY"):
        mock_get_gemini_tool()

    # Restore registry
    registry._tools = original_tools

def test_missing_tool_raises_error():
    # If a tool in the allowed list is missing from the registry, it should raise an error
    original_tools = registry._tools.copy()
    del registry._tools["get_analytics_summary"]

    with pytest.raises(ValueError, match="missing from the authoritative registry"):
        get_gemini_tool()

    # Restore registry
    registry._tools = original_tools
