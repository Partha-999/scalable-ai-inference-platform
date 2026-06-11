from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Modality(str, Enum):
    vision = "vision"
    text = "text"


class InferenceResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    tenant_id: str
    model_id: str
    modality: Modality
    label: str
    confidence: float
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    cached: bool = False
    latency_ms: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ModelRecord(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    modality: Modality
    framework: str
    version: str
    enabled: bool = True
    ab_group: str = "control"
    endpoint_name: str | None = None
    task: str | None = None
    description: str | None = None
