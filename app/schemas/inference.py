from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.domain import Modality


class InferenceMode(str, Enum):
    realtime = "realtime"
    batch = "batch"


class TextInferenceRequest(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "examples": [
                {"text": "I love this product", "use_ab_test": False},
                {
                    "question": "What is the capital of France?",
                    "context": "Paris is the capital and most populous city of France.",
                    "model_id": "text-qa-v1",
                },
            ]
        },
    )

    text: str | None = Field(
        default=None, min_length=1, examples=["I love this product"]
    )
    question: str | None = Field(
        default=None, examples=["What is the capital of France?"]
    )
    context: str | None = Field(
        default=None,
        examples=["Paris is the capital and most populous city of France."],
    )
    model_id: str | None = None
    tenant_id: str | None = None
    use_ab_test: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload(self) -> "TextInferenceRequest":
        if self.text:
            return self
        if self.question and self.context:
            return self
        raise ValueError("Provide either text or question/context")


class VisionInferenceRequest(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "examples": [
                {
                    "image_base64": "<base64-encoded-jpg-or-png>",
                    "model_id": "vision-vit-v1",
                }
            ]
        },
    )

    image_base64: str = Field(
        min_length=1,
        examples=["<base64-encoded-jpg-or-png>"],
    )
    model_id: str | None = None
    tenant_id: str | None = None
    use_ab_test: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchInferenceItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    modality: Modality
    text: str | None = None
    question: str | None = None
    context: str | None = None
    image_base64: str | None = None
    model_id: str | None = None
    use_ab_test: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_item(self) -> "BatchInferenceItem":
        if self.modality == Modality.vision and not self.image_base64:
            raise ValueError("image_base64 is required for vision items")
        if self.modality == Modality.text and not (
            self.text or (self.question and self.context)
        ):
            raise ValueError("text or question/context is required for text items")
        return self


class BatchInferenceRequest(BaseModel):
    tenant_id: str | None = None
    items: list[BatchInferenceItem]


class PredictionResponse(BaseModel):
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


class BatchInferenceResponse(BaseModel):
    request_id: str
    results: list[PredictionResponse]
