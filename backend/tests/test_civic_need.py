import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from backend.app.models.signal import StoredCitizenSignal
from backend.app.models.civic_need import CivicNeedExtraction, CivicNeed
from backend.app.analytics.interpreter import MockInterpreter, GeminiInterpreter, InterpretationError

def create_mock_signal(source="TEXT", raw_text="We need water."):
    return StoredCitizenSignal(
        signal_id="sig-123",
        idempotency_key="key",
        source=source,
        is_synthetic=False,
        raw_text=raw_text,
        detected_language="en",
        extraction_status="RECEIVED",
        submitted_at=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        processing_version="v1"
    )

def test_mock_interpreter_valid_signal():
    interpreter = MockInterpreter()
    signal = create_mock_signal(raw_text="Water supply is broken.")

    need = interpreter.interpret(signal)
    assert need.canonical_need_type == "WATER_SUPPLY_DEFICIT"
    assert need.sector == "WATER"
    assert need.source_signal_id == signal.signal_id
    assert need.processing_version == "interpreter.mock.v1"
    assert need.detected_language == "en"

def test_mock_interpreter_multilingual_normalization():
    interpreter = MockInterpreter()
    # Mock interpreter logic handles "తాగునీరు" -> WATER_SUPPLY_DEFICIT
    signal = create_mock_signal(raw_text="తాగునీరు సరిగా రావడం లేదు")
    signal.detected_language = "te"

    need = interpreter.interpret(signal)
    assert need.canonical_need_type == "WATER_SUPPLY_DEFICIT"
    assert need.sector == "WATER"
    assert need.detected_language == "te"
    assert need.need_label_en == "Water Supply Deficit"

def test_civic_need_extraction_validation():
    # Valid
    ext = CivicNeedExtraction(
        need_type="WATER_SUPPLY_DEFICIT",
        need_description="Missing drinking water",
        location_expression="Addateegala",
        location_confidence=0.9,
        urgency="HIGH",
        detected_language="en",
        is_multi_need=False
    )
    assert ext.need_type == "WATER_SUPPLY_DEFICIT"

    # Unknown category rejected
    with pytest.raises(ValidationError):
        CivicNeedExtraction(
            need_type="FLYING_CARS_DEFICIT", # Invalid enum
            need_description="Missing drinking water",
            location_expression="Addateegala",
            location_confidence=0.9,
            urgency="HIGH",
            detected_language="en",
            is_multi_need=False
        )

    # Excessive text rejected
    with pytest.raises(ValidationError):
        CivicNeedExtraction(
            need_type="WATER_SUPPLY_DEFICIT",
            need_description="A" * 600, # Over 500 max
            location_expression="Addateegala",
            location_confidence=0.9,
            urgency="HIGH",
            detected_language="en",
            is_multi_need=False
        )

    # Extra fields rejected (strict model by default or through validation)
    with pytest.raises(ValidationError):
        CivicNeedExtraction(
            need_type="WATER_SUPPLY_DEFICIT",
            need_description="Missing drinking water",
            location_expression="Addateegala",
            location_confidence=0.9,
            urgency="HIGH",
            detected_language="en",
            is_multi_need=False,
            unsupported_field="This should fail"
        )

def test_interpreter_voice_boundary():
    interpreter = MockInterpreter()
    signal = create_mock_signal(source="VOICE", raw_text="")

    with pytest.raises(InterpretationError, match="without normalized text transcript"):
        interpreter.interpret(signal)

def test_interpreter_messaging_boundary():
    interpreter = MockInterpreter()
    signal = create_mock_signal(source="MESSAGING", raw_text="")

    with pytest.raises(InterpretationError, match="without raw text"):
        interpreter.interpret(signal)

def test_gemini_interpreter_schema_generation():
    from unittest.mock import MagicMock
    interpreter = GeminiInterpreter(client=MagicMock(), gemini_model="gemini-3.1-flash-lite")
    # Ensure config has response_json_schema and it's a dict
    assert isinstance(interpreter.config.response_json_schema, dict)
    assert getattr(interpreter.config, "response_schema", None) is None

    # Ensure interpret raises InterpretationError when mocked client returns MagicMock text
    signal = create_mock_signal()
    with pytest.raises(InterpretationError, match="Gemini API or validation failed"):
        interpreter.interpret(signal)
