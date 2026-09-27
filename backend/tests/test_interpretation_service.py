import pytest
import os
import tempfile
from datetime import datetime, timezone
from pydantic import ValidationError

from backend.app.models.signal import StoredCitizenSignal
from backend.app.models.civic_need import CivicNeed, CivicNeedExtraction
from backend.app.analytics.interpreter import MockInterpreter, SignalInterpreter, InterpretationError
from backend.app.data.civic_need_repository import CivicNeedRepository
from backend.app.services.interpretation_service import CivicNeedInterpretationService

@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmpdirname:
        repo = CivicNeedRepository(storage_dir=tmpdirname)
        yield repo

@pytest.fixture
def service(temp_repo):
    interpreter = MockInterpreter()
    return CivicNeedInterpretationService(interpreter=interpreter, repository=temp_repo)

def create_mock_signal(
    signal_id="sig-123",
    source="TEXT",
    raw_text="We need water.",
    detected_language="en",
    is_synthetic=False
):
    return StoredCitizenSignal(
        signal_id=signal_id,
        idempotency_key=signal_id + "-key",
        source=source,
        is_synthetic=is_synthetic,
        raw_text=raw_text,
        detected_language=detected_language,
        extraction_status="RECEIVED",
        submitted_at=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        processing_version="v1"
    )

def test_interpret_valid_signal(service, temp_repo):
    signal = create_mock_signal(is_synthetic=True)
    success, civic_need, status = service.interpret_signal(signal)

    assert success is True
    assert status == "INTERPRETED"
    assert civic_need is not None

    assert civic_need.canonical_need_type == "WATER_SUPPLY_DEFICIT"
    assert civic_need.source_signal_id == signal.signal_id
    assert civic_need.detected_language == "en"

    # Check persistence
    persisted = temp_repo.get_by_source_signal_id(signal.signal_id)
    assert persisted is not None
    assert persisted.canonical_need_type == "WATER_SUPPLY_DEFICIT"

def test_idempotency_duplicate_interpretation(service, temp_repo):
    signal = create_mock_signal()
    # First interpretation
    success1, civic_need1, status1 = service.interpret_signal(signal)
    assert success1 is True

    # Mutate signal text to something else just to prove we don't re-interpret
    signal.raw_text = "Now we need roads"

    # Second interpretation
    success2, civic_need2, status2 = service.interpret_signal(signal)
    assert success2 is True
    assert civic_need2.need_id == civic_need1.need_id
    assert civic_need2.canonical_need_type == "WATER_SUPPLY_DEFICIT" # Did not change to roads

def test_voice_without_text_fails(service):
    signal = create_mock_signal(source="VOICE", raw_text="")
    success, civic_need, status = service.interpret_signal(signal)

    assert success is False
    assert status == "FAILED"
    assert civic_need is None

def test_messaging_without_text_fails(service):
    signal = create_mock_signal(source="MESSAGING", raw_text="")
    success, civic_need, status = service.interpret_signal(signal)

    assert success is False
    assert status == "FAILED"

class MalformedMockInterpreter(SignalInterpreter):
    def interpret(self, signal: StoredCitizenSignal) -> CivicNeed:
        # Purposely return something invalid to cause Pydantic validation failure
        # (Though our mocked return type says CivicNeed, we'll raise an exception simulating
        # failure in validation step which normally happens in GeminiInterpreter)
        raise ValidationError.from_exception_data(
            title="CivicNeedExtraction",
            line_errors=[]
        )

def test_malformed_interpreter_result_fails_closed(temp_repo):
    interpreter = MalformedMockInterpreter()
    bad_service = CivicNeedInterpretationService(interpreter, temp_repo)
    signal = create_mock_signal()

    success, civic_need, status = bad_service.interpret_signal(signal)
    assert success is False
    assert status == "FAILED"

def test_multilingual_language_preservation(service):
    signal = create_mock_signal(raw_text="తాగునీరు", detected_language="te")
    success, civic_need, status = service.interpret_signal(signal)

    assert success is True
    assert civic_need.detected_language == "te"

def test_geography_preservation(service):
    signal = create_mock_signal(raw_text="Water needed in Addateegala")
    success, civic_need, status = service.interpret_signal(signal)

    assert success is True
    assert civic_need.location_expression == "addateegala"

def test_multi_need_flag_preservation(service):
    signal = create_mock_signal()
    success, civic_need, status = service.interpret_signal(signal)

    assert success is True
    assert civic_need.is_composite is False # MockInterpreter currently hardcodes False
