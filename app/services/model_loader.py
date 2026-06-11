from __future__ import annotations

import os
import io
import logging
from contextlib import nullcontext
from dataclasses import dataclass
from threading import Lock, RLock
from typing import Any

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")

from PIL import Image
from transformers import pipeline

from app.core.config import Settings, get_settings
from app.models.domain import Modality, ModelRecord
from app.services.model_registry import infer_model_task

logger = logging.getLogger(__name__)


SEMANTIC_TASK_TO_HF_TASK = {
    "sentiment": "text-classification",
    "topic": "text-classification",
    "intent": "text-classification",
    "question-answering": "question-answering",
    "token-classification": "token-classification",
    "image-classification": "image-classification",
    "text-classification": "text-classification",
    "object-detection": "object-detection",
    "ocr": "ocr",
}


@dataclass(slots=True)
class LoadedPipeline:
    task: str
    model_name: str
    runner: Any


class ModelLoader:
    _instance: ModelLoader | None = None
    _instance_lock: Lock = Lock()

    def __new__(cls, settings: Settings | None = None) -> "ModelLoader":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialize(settings or get_settings())
                    cls._instance = instance
        return cls._instance

    def _initialize(self, settings: Settings) -> None:
        self.settings = settings
        self._pipelines: dict[str, LoadedPipeline] = {}
        self._locks: dict[str, RLock] = {}
        self._registry_lock = Lock()

    def _pipeline_lock(self, model_key: str) -> RLock:
        lock = self._locks.get(model_key)
        if lock is None:
            with self._registry_lock:
                lock = self._locks.get(model_key)
                if lock is None:
                    lock = RLock()
                    self._locks[model_key] = lock
        return lock

    def _torch_context(self):
        try:
            import torch

            return torch.no_grad()
        except Exception:
            return nullcontext()

    def _device_index(self) -> int:
        try:
            import torch

            return 0 if torch.cuda.is_available() else -1
        except Exception:
            return -1

    def _torch_dtype(self) -> Any | None:
        try:
            import torch

            return torch.float16 if torch.cuda.is_available() else torch.float32
        except Exception:
            return None

    def _resolve_task(self, model: ModelRecord) -> str:
        return infer_model_task(model)

    def _hf_task(self, task: str) -> str:
        return SEMANTIC_TASK_TO_HF_TASK.get(task, "text-classification")

    def _load_pipeline(self, model: ModelRecord) -> LoadedPipeline:
        semantic_task = self._resolve_task(model)
        task = self._hf_task(semantic_task)
        model_name = model.endpoint_name or model.model_id
        logger.info(
            "Loading inference pipeline model_id=%s semantic_task=%s hf_task=%s endpoint=%s",
            model.model_id,
            semantic_task,
            task,
            model_name,
        )
        if semantic_task == "ocr":
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            import easyocr
            try:
                processor = TrOCRProcessor.from_pretrained(model_name)
                trocr_model = VisionEncoderDecoderModel.from_pretrained(model_name)
                device = self._device_index()
                if device >= 0:
                    trocr_model = trocr_model.to(f"cuda:{device}")
                
                gpu_enabled = (device >= 0)
                detector = easyocr.Reader(['en'], gpu=gpu_enabled)
                
                runner = {
                    "processor": processor,
                    "model": trocr_model,
                    "detector": detector
                }
            except Exception as e:
                if isinstance(e, AttributeError) and "endswith" in str(e):
                    from app.core.exceptions import ModelArtifactsMissingError
                    raise ModelArtifactsMissingError(
                        f"Model weights file not found in local cache for '{model_name}'. "
                        "The cache may be corrupt or incomplete."
                    ) from e
                raise
            return LoadedPipeline(task=task, model_name=model_name, runner=runner)

        runner_kwargs: dict[str, Any] = {
            "task": task,
            "model": model_name,
            "device": self._device_index(),
        }
        dtype = self._torch_dtype()
        if dtype is not None:
            runner_kwargs["model_kwargs"] = {"torch_dtype": dtype}
        try:
            runner = pipeline(**runner_kwargs)
        except AttributeError as e:
            from app.core.exceptions import ModelArtifactsMissingError
            raise ModelArtifactsMissingError(
                f"Model weights file not found in local cache for '{model_name}'. "
                "The cache may be corrupt or incomplete."
            ) from e
        return LoadedPipeline(task=task, model_name=model_name, runner=runner)

    def get_pipeline(self, model: ModelRecord) -> LoadedPipeline:
        model_key = model.model_id
        if model_key in self._pipelines:
            return self._pipelines[model_key]

        lock = self._pipeline_lock(model_key)
        with lock:
            cached = self._pipelines.get(model_key)
            if cached is not None:
                return cached
            loaded = self._load_pipeline(model)
            self._pipelines[model_key] = loaded
            return loaded

    def clear_cache(self) -> None:
        with self._registry_lock:
            self._pipelines.clear()
            self._locks.clear()
        import gc
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def predict_text(
        self,
        model: ModelRecord,
        text: str | None = None,
        question: str | None = None,
        context: str | None = None,
    ) -> list[dict[str, Any]]:
        bundle = self.get_pipeline(model)
        task = bundle.task

        with self._torch_context():
            if task == "question-answering":
                if not question or not context:
                    raise ValueError("question and context are required for QA models")
                raw_output = bundle.runner(question=question, context=context)
            elif task == "token-classification":
                prompt = text or question or ""
                raw_output = bundle.runner(prompt)
            else:
                prompt = text or question or ""
                raw_output = bundle.runner(prompt, top_k=5)

        return self._normalize_output(task, raw_output)

    def predict_image(
        self, model: ModelRecord, image_bytes: bytes
    ) -> list[dict[str, Any]]:
        bundle = self.get_pipeline(model)
        if bundle.task not in {"image-classification", "object-detection", "ocr"}:
            raise ValueError(
                f"Model {model.model_id} is not configured for vision inference"
            )

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        with self._torch_context():
            if bundle.task == "object-detection":
                raw_output = bundle.runner(image)
            elif bundle.task == "ocr":
                processor = bundle.runner["processor"]
                trocr_model = bundle.runner["model"]
                detector = bundle.runner["detector"]
                
                import numpy as np
                img_array = np.array(image)
                
                horizontal_list, _ = detector.detect(img_array)
                boxes = horizontal_list[0] if horizontal_list else []
                
                words_list = []
                scores = []
                device = self._device_index()
                
                for box in boxes:
                    x_min, x_max, y_min, y_max = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                    width, height = image.size
                    x_min = max(0, x_min)
                    y_min = max(0, y_min)
                    x_max = min(width, x_max)
                    y_max = min(height, y_max)
                    
                    if x_max <= x_min or y_max <= y_min:
                        continue
                        
                    cropped_image = image.crop((x_min, y_min, x_max, y_max))
                    
                    pixel_values = processor(images=cropped_image, return_tensors="pt").pixel_values
                    if device >= 0:
                        pixel_values = pixel_values.to(f"cuda:{device}")
                        
                    generated_ids = trocr_model.generate(pixel_values)
                    word_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                    word_text = word_text.strip()
                    
                    word_conf = 0.95
                    words_list.append({
                        "text": word_text,
                        "bbox": [x_min, y_min, x_max, y_max],
                        "confidence": word_conf
                    })
                    scores.append(word_conf)
                
                full_text = " ".join([w["text"] for w in words_list if w["text"]])
                avg_score = sum(scores) / len(scores) if scores else 1.0
                
                raw_output = {
                    "text": full_text,
                    "words": words_list,
                    "confidence": avg_score
                }
            else:
                raw_output = bundle.runner(image, top_k=5)
        return self._normalize_output(bundle.task, raw_output)

    def _normalize_output(self, task: str, raw_output: Any) -> list[dict[str, Any]]:
        if task == "ocr":
            if isinstance(raw_output, dict):
                return [
                    {
                        "label": "OCR_TEXT",
                        "text": raw_output.get("text", ""),
                        "score": raw_output.get("confidence", 0.95),
                        "words": raw_output.get("words", [])
                    }
                ]
            text = str(raw_output)
            return [
                {
                    "label": "OCR_TEXT",
                    "text": text,
                    "score": 0.95,
                    "words": []
                }
            ]

        if task == "question-answering":
            if isinstance(raw_output, dict):
                return [
                    {
                        "label": raw_output.get("answer", ""),
                        "score": float(raw_output.get("score", 0.0)),
                        "answer": raw_output.get("answer", ""),
                        "start": raw_output.get("start"),
                        "end": raw_output.get("end"),
                    }
                ]
            return [{"label": str(raw_output), "score": 0.0, "answer": str(raw_output)}]

        if isinstance(raw_output, dict):
            raw_items = [raw_output]
        elif (
            raw_output
            and isinstance(raw_output, list)
            and raw_output
            and isinstance(raw_output[0], list)
        ):
            raw_items = raw_output[0]
        else:
            raw_items = raw_output or []

        normalized: list[dict[str, Any]] = []
        for item in raw_items[:5]:
            if not isinstance(item, dict):
                continue
            label = (
                item.get("label")
                or item.get("entity_group")
                or item.get("entity")
                or "unknown"
            )
            normalized.append(
                {
                    "label": label,
                    "score": float(item.get("score", 0.0)),
                    **{k: v for k, v in item.items() if k not in {"label", "score"}},
                }
            )
        return normalized
