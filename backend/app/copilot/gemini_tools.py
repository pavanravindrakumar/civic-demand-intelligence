from google.genai import types
from backend.app.copilot.executor import registry
from backend.app.copilot.tools import ToolAuthorization

def get_gemini_tool() -> types.Tool:
    """
    Converts the authoritative deterministic CopilotToolRegistry into a
    Google GenAI SDK Tool object containing FunctionDeclarations.

    This acts only as a model-facing schema description. It is NOT the security boundary.
    The deterministic CopilotExecutor handles all execution and safety.
    """
    allowed_tool_names = [
        "get_analytics_summary",
        "get_village_analytics",
        "get_analytics_readiness"
    ]

    declarations = []

    for tool_name in allowed_tool_names:
        tool_def = registry.get_tool(tool_name)
        if not tool_def:
            raise ValueError(f"CRITICAL: Tool '{tool_name}' is missing from the authoritative registry.")

        # Security validation: Only expose READ_ONLY tools to the model
        if tool_def.authorization != ToolAuthorization.READ_ONLY:
            raise ValueError(f"CRITICAL: Tool '{tool_name}' is not READ_ONLY. Do not expose to the model in this phase.")

        # Pydantic JSON schema automatically converts nicely to google.genai.types.Schema
        schema_dict = tool_def.input_schema.model_json_schema()

        declaration = types.FunctionDeclaration(
            name=tool_def.name,
            description=tool_def.description,
            parameters_json_schema=schema_dict
        )
        declarations.append(declaration)

    return types.Tool(
        function_declarations=declarations
    )
