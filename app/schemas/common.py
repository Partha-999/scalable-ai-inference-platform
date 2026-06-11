from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResponseStatus(str, Enum):
    success = "success"
    queued = "queued"
    failed = "failed"


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service: str = "ai-inference-platform"


class ErrorResponse(BaseModel):
    detail: str
    trace_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
