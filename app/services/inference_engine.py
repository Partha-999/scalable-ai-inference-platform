from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.domain import ModelRecord
from app.services.model_loader import ModelLoader


@dataclass(slots=True)
class PredictionBundle:
    label: str
    confidence: float
    predictions: list[dict[str, Any]]


class InferenceEngine:
    def __init__(self, loader: ModelLoader) -> None:
        self.loader = loader

    def predict_text(
        self,
        model: ModelRecord,
        text: str | None = None,
        question: str | None = None,
        context: str | None = None,
    ) -> PredictionBundle:
        predictions = self.loader.predict_text(
            model, text=text, question=question, context=context
        )
        return self._bundle(predictions)

    def predict_image(self, model: ModelRecord, image_bytes: bytes) -> PredictionBundle:
        predictions = self.loader.predict_image(model, image_bytes)
        return self._bundle(predictions)

    def _bundle(self, predictions: list[dict[str, Any]]) -> PredictionBundle:
        if not predictions:
            return PredictionBundle(label="unknown", confidence=0.0, predictions=[])
        top_prediction = predictions[0]
        label = str(
            top_prediction.get("label") or top_prediction.get("answer") or "unknown"
        )
        confidence = float(top_prediction.get("score", 0.0))
        return PredictionBundle(
            label=label, confidence=confidence, predictions=predictions
        )
