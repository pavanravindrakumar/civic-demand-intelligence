from typing import Any, Dict, Type
from pydantic import BaseModel

def generate_gemini_json_schema(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Converts a strict Pydantic model into a dictionary suitable for
    google.genai SDK's `response_json_schema` field.

    This preserves security-critical constraints like additionalProperties=False
    which are sometimes lost or improperly serialized (e.g. to additional_properties)
    if the Pydantic model is passed directly to `response_schema`.
    """
    schema = model_class.model_json_schema()

    # We do not strip additionalProperties. The raw JSON Schema dictionary
    # correctly maintains 'additionalProperties' in camelCase.
    # The SDK's response_json_schema expects this standard format.

    return schema
