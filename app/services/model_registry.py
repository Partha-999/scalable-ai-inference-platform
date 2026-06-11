from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel

from app.models.domain import Modality, ModelRecord


def infer_model_task(model: ModelRecord) -> str:
    if getattr(model, "task", None):
        return model.task
    name = f"{model.model_id}:{model.endpoint_name or ''}".lower()
    if model.modality == Modality.vision:
        if "detect" in name or "detr" in name:
            return "object-detection"
        return "image-classification"
    if any(token in name for token in ("squad", "qa", "question")):
        return "question-answering"
    if any(token in name for token in ("ner", "entity", "token-classification")):
        return "token-classification"
    if any(token in name for token in ("sentiment", "sst", "emotion", "polarity")):
        return "sentiment"
    if any(token in name for token in ("topic", "zero-shot")):
        return "topic"
    if any(token in name for token in ("intent", "utterance", "instruct")):
        return "intent"
    return "text-classification"


class ModelRegistry(BaseModel):
    models: list[ModelRecord]

    @classmethod
    def load(cls, path: Path) -> "ModelRegistry":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(models=[ModelRecord(**item) for item in payload["models"]])

    def list_models(self) -> list[ModelRecord]:
        return [model for model in self.models if model.enabled]

    def by_modality(self, modality: Modality) -> list[ModelRecord]:
        return [model for model in self.list_models() if model.modality == modality]

    def resolve(
        self,
        modality: Modality,
        tenant_id: str,
        preferred_model_id: str | None = None,
        use_ab_test: bool = True,
        task_hint: str | None = None,
    ) -> ModelRecord:
        candidates = self.by_modality(modality)
        if preferred_model_id:
            for model in candidates:
                if model.model_id == preferred_model_id:
                    return model

        if modality == Modality.text:
            candidates = [
                model
                for model in candidates
                if infer_model_task(model) != "token-classification"
            ]
        if task_hint:
            matched = [
                model for model in candidates if infer_model_task(model) == task_hint
            ]
            if matched:
                candidates = matched
        if not candidates:
            raise ValueError(f"No enabled models for modality={modality}")
        if not use_ab_test:
            return candidates[0]
        seed = hashlib.sha256(f"{tenant_id}:{modality}".encode("utf-8")).hexdigest()
        index = int(seed, 16) % len(candidates)
        return candidates[index]

    def model_ids(self) -> Iterable[str]:
        for model in self.list_models():
            yield model.model_id
