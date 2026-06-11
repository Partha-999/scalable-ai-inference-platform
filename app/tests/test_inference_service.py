from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.services.cache import CacheValue
from app.models.domain import ModelRecord
from app.services.inference_service import InferenceDependencies, InferenceService


class FakeRegistry:
    def resolve(
        self,
        modality,
        tenant_id,
        preferred_model_id=None,
        use_ab_test=True,
        task_hint=None,
    ):
        return ModelRecord(
            model_id=preferred_model_id or "text-sentiment-v1",
            modality=modality,
            framework="transformers",
            version="1.0.0",
            endpoint_name="distilbert-base-uncased-finetuned-sst-2-english",
        )


class SentimentRoutingRegistry:
    def resolve(
        self,
        modality,
        tenant_id,
        preferred_model_id=None,
        use_ab_test=True,
        task_hint=None,
    ):
        if task_hint == "sentiment":
            return ModelRecord(
                model_id="text-sentiment-v1",
                modality=modality,
                framework="transformers",
                version="1.0.0",
                endpoint_name="distilbert-base-uncased-finetuned-sst-2-english",
            )

        return ModelRecord(
            model_id="text-entity-v1",
            modality=modality,
            framework="transformers",
            version="1.0.0",
            endpoint_name="dslim/bert-base-NER",
        )


class FakeCache:
    async def get(self, key):
        return None

    async def set(self, key, value):
        return None


class RaisingEngine:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def predict_text(self, model, text=None, question=None, context=None):
        raise self.exc

    def predict_image(self, model, image_bytes):
        raise self.exc


class SentimentEngine:
    def predict_text(self, model, text=None, question=None, context=None):
        lowered = (text or "").lower()
        if "hate" in lowered:
            return type(
                "PredictionBundle",
                (),
                {
                    "label": "NEGATIVE",
                    "confidence": 0.99,
                    "predictions": [{"label": "NEGATIVE", "score": 0.99}],
                },
            )()
        return type(
            "PredictionBundle",
            (),
            {
                "label": "POSITIVE",
                "confidence": 0.99,
                "predictions": [{"label": "POSITIVE", "score": 0.99}],
            },
        )()

    def predict_image(self, model, image_bytes):
        raise RuntimeError("not used")


class CacheHitCache:
    async def get(self, key):
        return CacheValue(
            value={
                "request_id": "cached-req",
                "tenant_id": "tenant-a",
                "model_id": "text-sentiment-v1",
                "modality": "text",
                "label": "positive",
                "confidence": 0.99,
                "predictions": [{"label": "positive", "score": 0.99}],
                "cached": False,
                "latency_ms": 1.23,
            },
            cached=True,
        )

    async def set(self, key, value):
        return None


@pytest.mark.asyncio
async def test_text_inference_propagates_runtime_errors():
    service = InferenceService(
        get_settings(),
        InferenceDependencies(
            registry=FakeRegistry(),
            cache=FakeCache(),
            engine=RaisingEngine(RuntimeError("hf pipeline crashed")),
        ),
    )

    with pytest.raises(RuntimeError, match="hf pipeline crashed"):
        await service.infer_text(
            "I love this product", tenant_id="tenant-a", use_ab_test=False
        )


@pytest.mark.asyncio
async def test_text_inference_converts_validation_errors_to_400():
    service = InferenceService(
        get_settings(),
        InferenceDependencies(
            registry=FakeRegistry(),
            cache=FakeCache(),
            engine=RaisingEngine(
                ValueError("question and context are required for QA models")
            ),
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.infer_text(
            "",
            tenant_id="tenant-a",
            question="What is the capital of France?",
            context="",
            use_ab_test=False,
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_text_inference_cache_hit_overrides_cached_flag_only():
    service = InferenceService(
        get_settings(),
        InferenceDependencies(
            registry=FakeRegistry(),
            cache=CacheHitCache(),
            engine=RaisingEngine(RuntimeError("should not execute on cache hit")),
        ),
    )

    result = await service.infer_text(
        "I love this product", tenant_id="tenant-a", use_ab_test=False
    )

    assert result.cached is True
    assert result.label == "positive"
    assert result.model_id == "text-sentiment-v1"


@pytest.mark.asyncio
async def test_plain_text_inference_routes_to_sentiment_model():
    service = InferenceService(
        get_settings(),
        InferenceDependencies(
            registry=SentimentRoutingRegistry(),
            cache=FakeCache(),
            engine=SentimentEngine(),
        ),
    )

    negative = await service.infer_text(
        "I hate you", tenant_id="tenant-a", use_ab_test=False
    )
    positive = await service.infer_text(
        "I love this", tenant_id="tenant-a", use_ab_test=False
    )

    assert negative.model_id == "text-sentiment-v1"
    assert negative.label == "NEGATIVE"
    assert positive.model_id == "text-sentiment-v1"
    assert positive.label == "POSITIVE"
