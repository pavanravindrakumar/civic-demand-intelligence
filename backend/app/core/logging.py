import logging
import json
import os
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        req_id = request_id_ctx_var.get()
        if req_id:
            log_obj["request_id"] = req_id

        if hasattr(record, "operation"):
            log_obj["operation"] = record.operation

        if hasattr(record, "error_code"):
            log_obj["error_code"] = record.error_code

        return json.dumps(log_obj)

class SimpleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx_var.get()
        prefix = f"[{req_id}] " if req_id else ""
        record.msg = f"{prefix}{record.msg}"
        return super().format(record)

def setup_logging():
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    env = os.environ.get("ENV", "production").lower()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()

    if env == "development" or env == "local":
        handler.setFormatter(SimpleFormatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    else:
        handler.setFormatter(JSONFormatter())

    root_logger.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)

def get_logger(name: str):
    return logging.getLogger(name)
