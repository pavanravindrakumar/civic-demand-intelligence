import pytest
from pydantic import BaseModel, ConfigDict, Field
from google.genai import types
from backend.app.ai.schema_adapter import generate_gemini_json_schema
from backend.app.models.civic_need import CivicNeedExtraction

class DummyNested(BaseModel):
    model_config = ConfigDict(extra='forbid')
    value: int

class DummyModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(..., description="A name")
    category: str = Field(..., pattern=r"^[A-Z]+$")
    nested: DummyNested

def test_schema_adapter_preserves_additional_properties_false():
    schema = generate_gemini_json_schema(DummyModel)

    assert schema.get("additionalProperties") is False
    assert schema["properties"]["name"]["description"] == "A name"

def test_schema_adapter_preserves_nested_defs():
    schema = generate_gemini_json_schema(DummyModel)

    assert "$defs" in schema
    assert "DummyNested" in schema["$defs"]
    assert schema["$defs"]["DummyNested"].get("additionalProperties") is False

def test_schema_adapter_does_not_mutate_original_model():
    # Calling the adapter multiple times should be safe
    schema1 = generate_gemini_json_schema(CivicNeedExtraction)
    schema2 = generate_gemini_json_schema(CivicNeedExtraction)

    assert schema1 == schema2
    # Ensure it's returning a standard dict structure
    assert isinstance(schema1, dict)

def test_google_genai_config_accepts_adapter_output():
    schema = generate_gemini_json_schema(CivicNeedExtraction)

    # We test that the SDK accepts the generated schema dict in response_json_schema
    # and DOES NOT place it in response_schema
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=schema
    )

    assert config.response_json_schema == schema
    assert getattr(config, "response_schema", None) is None

def test_civic_need_extraction_rejects_extra_after_generation():
    # Simulate a generated JSON from Gemini that includes an extra field despite instructions
    generated_json = {
        "need_type": "WATER_SUPPLY_DEFICIT",
        "need_description": "We need water",
        "location_expression": "Village",
        "location_confidence": 0.9,
        "urgency": "HIGH",
        "detected_language": "en",
        "is_multi_need": False,
        "extra_field": "This should be rejected"
    }

    from pydantic import ValidationError
    with pytest.raises(ValidationError) as exc_info:
        CivicNeedExtraction.model_validate(generated_json)

    assert "extra_field" in str(exc_info.value)

def test_malformed_model_output_fails_closed():
    # Simulate Gemini generating an invalid enum value
    generated_json = {
        "need_type": "INVALID_NEED_TYPE",
        "need_description": "We need water",
        "location_expression": "Village",
        "location_confidence": 0.9,
        "urgency": "HIGH",
        "detected_language": "en",
        "is_multi_need": False
    }

    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CivicNeedExtraction.model_validate(generated_json)
