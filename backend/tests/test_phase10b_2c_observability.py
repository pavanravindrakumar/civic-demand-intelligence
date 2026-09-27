import os
import json
import pytest
import logging
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.logging import JSONFormatter, request_id_ctx_var, setup_logging
from backend.app.data.evidence_ledger_repository import EvidenceLedgerRepository
from backend.app.copilot.service import GeminiCopilotService
from backend.app.copilot.orchestrator import ConversationTurn, ModelResponse

@pytest.fixture
def client():
    return TestClient(app)

def test_json_formatter_valid_structure():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger", level=logging.INFO, pathname="test.py", lineno=1,
        msg="Test message", args=(), exc_info=None
    )
    request_id_ctx_var.set("test-123")

    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["message"] == "Test message"
    assert data["severity"] == "INFO"
    assert data["logger"] == "test_logger"
    assert "timestamp" in data
    assert data["request_id"] == "test-123"

def test_jsonl_corruption_handling(tmp_path):
    repo_dir = tmp_path / "data"
    repo_dir.mkdir()
    repo = EvidenceLedgerRepository(storage_dir=str(repo_dir))

    with open(repo.file_path, "w", encoding="utf-8") as f:
        f.write('{"priority_assessment_id": "test", "calculation_version": "1", "priority_version": "1", "record_hash": "hash"}\n')
        f.write('{"broken JSON \n')

    with patch("backend.app.data.evidence_ledger_repository.logger") as mock_logger:
        repo.load_all()
        # Should skip the broken line and log a warning
        mock_logger.warning.assert_called_with(
            "Malformed JSONL line skipped",
            extra={"safe_context": {"repository": "EvidenceLedgerRepository", "line_number": 2}}
        )

def test_gemini_failure_logging_and_safe_response():
    config = MagicMock()
    with patch("backend.app.copilot.service.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Simulate a Gemini provider failure
        mock_client.models.generate_content.side_effect = Exception("Secret raw exception")

        from backend.app.copilot.service import GeminiModelAdapter
        adapter = GeminiModelAdapter(config)

        with patch("backend.app.copilot.service.logger") as mock_logger:
            resp = adapter.generate_response([])

            # The client gets a safe message
            assert "The AI provider is currently unavailable" in resp.text

            # The log contains the exception TYPE but not the string
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Secret raw exception" not in str(call_args)
            assert call_args[1]["extra"]["safe_context"]["error_type"] == "Exception"

def test_copilot_safety_event_logging():
    config = MagicMock()
    with patch("backend.app.copilot.service.get_client"):
        service = GeminiCopilotService(config=config, max_rounds=1)

        # Force a function call to consume the round
        with patch.object(service.adapter, "generate_response") as mock_gen:
            from backend.app.copilot.orchestrator import FunctionCallRequest
            mock_gen.return_value = ModelResponse(function_calls=[
                FunctionCallRequest(id="1", name="search_villages", args={})
            ])

            with patch("backend.app.copilot.orchestrator.CopilotExecutor.execute") as mock_exec:
                mock_res = MagicMock()
                mock_res.status = "SUCCESS"
                mock_res.model_dump.return_value = {"ok": True}
                mock_exec.return_value = mock_res

                with patch("backend.app.copilot.service.logger") as mock_logger:
                    service.process_message("test")

                    mock_logger.warning.assert_called_with(
                        "Copilot Safety Event",
                        extra={"safe_context": {"operation": "copilot", "reason": "Error: Maximum tool rounds exceeded. Safety limit triggered."}}
                    )
