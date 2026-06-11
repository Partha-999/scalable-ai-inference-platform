from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

TRACE_ID: ContextVar[str] = ContextVar("trace_id", default="-")
TENANT_ID: ContextVar[str] = ContextVar("tenant_id", default="anonymous")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", TRACE_ID.get()),
            "tenant_id": getattr(record, "tenant_id", TENANT_ID.get()),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = TRACE_ID.get()
        record.tenant_id = TENANT_ID.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(ContextFilter())
    root_logger.addHandler(handler)

    for noisy_logger in ("uvicorn", "uvicorn.error", "uvicorn.access", "asyncio"):
        logging.getLogger(noisy_logger).handlers.clear()
        logging.getLogger(noisy_logger).propagate = True
