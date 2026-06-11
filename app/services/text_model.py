from __future__ import annotations

from typing import Any


class TextModelService:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: Any | None = None
        self._tokenizer: Any | None = None

    def _load(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        try:
            from transformers import TFAutoModelForSequenceClassification, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = TFAutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
        except Exception:
            self._model = "fallback"
            self._tokenizer = "fallback"

    def _fallback_predict(self, text: str) -> list[dict[str, Any]]:
        lowered = text.lower()
        positive = sum(
            word in lowered
            for word in ("good", "great", "excellent", "positive", "love")
        )
        negative = sum(
            word in lowered for word in ("bad", "poor", "hate", "negative", "error")
        )
        label = "positive" if positive >= negative else "negative"
        score = 0.55 + 0.1 * abs(positive - negative)
        return [
            {"label": label, "score": min(score, 0.99)},
            {"label": "neutral", "score": 1.0 - min(score, 0.99)},
        ]

    def predict(self, text: str) -> list[dict[str, Any]]:
        self._load()
        if self._model == "fallback" or self._tokenizer == "fallback":
            return self._fallback_predict(text)

        try:
            inputs = self._tokenizer(
                text, return_tensors="tf", truncation=True, padding=True
            )
            outputs = self._model(**inputs)
            import tensorflow as tf

            probabilities = tf.nn.softmax(outputs.logits[0]).numpy()
            id2label = self._model.config.id2label
            return [
                {"label": id2label.get(index, str(index)), "score": float(probability)}
                for index, probability in enumerate(probabilities)
            ]
        except Exception:
            return self._fallback_predict(text)
