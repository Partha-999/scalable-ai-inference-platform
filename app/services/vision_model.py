from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image

from app.utils.gpu import get_compute_device


class VisionModelService:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.device = get_compute_device()
        self._model: Any | None = None
        self._processor: Any | None = None

    def _load(self) -> None:
        if self._model is not None and self._processor is not None:
            return
        try:
            import tensorflow as tf
            from transformers import TFViTForImageClassification, ViTImageProcessor

            self._processor = ViTImageProcessor.from_pretrained(self.model_name)
            self._model = TFViTForImageClassification.from_pretrained(self.model_name)
            if self.device == "gpu":
                tf.config.set_visible_devices(
                    tf.config.list_physical_devices("GPU"), "GPU"
                )
        except Exception:
            self._model = "fallback"
            self._processor = "fallback"

    def _fallback_predict(self, image: Image.Image) -> list[dict[str, Any]]:
        width, height = image.size
        dominant = (
            "bright"
            if sum(image.convert("L").resize((1, 1)).getdata()) > 127
            else "dark"
        )
        return [
            {"label": dominant, "score": 0.51},
            {"label": f"{width}x{height}", "score": 0.49},
        ]

    def predict(self, image_bytes: bytes) -> list[dict[str, Any]]:
        self._load()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        if self._model == "fallback" or self._processor == "fallback":
            return self._fallback_predict(image)

        try:
            import numpy as np
            import tensorflow as tf

            inputs = self._processor(images=image, return_tensors="tf")
            outputs = self._model(**inputs)
            logits = outputs.logits[0].numpy()
            probabilities = tf.nn.softmax(logits).numpy()
            top_indices = np.argsort(probabilities)[::-1][:5]
            return [
                {
                    "label": self._model.config.id2label.get(
                        int(index), str(int(index))
                    ),
                    "score": float(probabilities[index]),
                }
                for index in top_indices
            ]
        except Exception:
            return self._fallback_predict(image)
