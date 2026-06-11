from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.domain import InferenceResult, Modality, ModelRecord
from app.services.cache import CacheValue


class FakeInferenceService:
    async def infer_text(
        self,
        text: str,
        tenant_id: str,
        request_id: str | None = None,
        model_id: str | None = None,
        use_ab_test: bool = True,
        question: str | None = None,
        context: str | None = None,
        metadata: dict | None = None,
    ) -> InferenceResult:
        if question and context:
            return InferenceResult(
                request_id=request_id or "req-qa",
                tenant_id=tenant_id,
                model_id=model_id or "text-qa-v1",
                modality=Modality.text,
                label="Paris",
                confidence=0.97,
                predictions=[{"label": "Paris", "score": 0.97, "answer": "Paris"}],
                cached=False,
                latency_ms=1.0,
            )
        return InferenceResult(
            request_id=request_id or "req-1",
            tenant_id=tenant_id,
            model_id=model_id or "text-sentiment-v1",
            modality=Modality.text,
            label="positive",
            confidence=0.99,
            predictions=[{"label": "positive", "score": 0.99}],
            cached=False,
            latency_ms=1.0,
        )

    async def infer_image(
        self,
        image_bytes: bytes,
        tenant_id: str,
        request_id: str | None = None,
        model_id: str | None = None,
        use_ab_test: bool = True,
    ) -> InferenceResult:
        return InferenceResult(
            request_id=request_id or "req-2",
            tenant_id=tenant_id,
            model_id=model_id or "vision-vit-v1",
            modality=Modality.vision,
            label="object",
            confidence=0.88,
            predictions=[{"label": "object", "score": 0.88}],
            cached=False,
            latency_ms=2.0,
        )

    async def batch_infer(self, items, tenant_id: str, request_id: str | None = None):
        return [await self.infer_text("hello", tenant_id, request_id=request_id)]

    @property
    def deps(self):
        class Registry:
            def list_models(self):
                from app.models.domain import ModelRecord

                return [
                    ModelRecord(
                        model_id="text-sentiment-v1",
                        modality=Modality.text,
                        framework="transformers",
                        version="1.0.0",
                    ),
                    ModelRecord(
                        model_id="vision-vit-v1",
                        modality=Modality.vision,
                        framework="tensorflow",
                        version="1.0.0",
                    ),
                ]

        return type("Deps", (), {"registry": Registry()})


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    app.state.inference_service = FakeInferenceService()
    return TestClient(app)


class MockRedis:
    def __init__(self, *args, **kwargs) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.store[key] = value
        if ex is not None:
            self.ttls[key] = ex
        return True

    async def incr(self, key: str) -> int:
        val = int(self.store.get(key, 0)) + 1
        self.store[key] = str(val)
        return val

    async def expire(self, key: str, seconds: int) -> bool:
        self.ttls[key] = seconds
        return True

    async def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch) -> MockRedis:
    import redis.asyncio as aioredis
    mock_client = MockRedis()
    monkeypatch.setattr(aioredis.Redis, "from_url", lambda *args, **kwargs: mock_client)
    return mock_client

