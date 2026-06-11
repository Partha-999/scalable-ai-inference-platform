from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.domain import Modality


class ModelInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    modality: Modality
    framework: str
    version: str
    enabled: bool = True
    ab_group: str = "control"
    endpoint_name: str | None = None
    description: str | None = None


class ModelRegistryResponse(BaseModel):
    models: list[ModelInfo]
