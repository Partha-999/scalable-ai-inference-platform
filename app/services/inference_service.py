from __future__ import annotations

import asyncio
import base64
import logging
import json
import hashlib
import time
import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status

from app.core.config import Settings
from app.monitoring.metrics import ACTIVE_REQUESTS, CACHE_HIT_RATE, INFERENCE_LATENCY
from app.models.domain import InferenceResult, Modality, ModelRecord
from app.schemas.inference import BatchInferenceItem
from app.services.cache import RedisCache
from app.services.model_registry import infer_model_task
from app.services.model_registry import ModelRegistry
from app.services.inference_engine import InferenceEngine

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InferenceDependencies:
    registry: ModelRegistry
    cache: RedisCache
    engine: InferenceEngine


class InferenceService:
    def __init__(self, settings: Settings, deps: InferenceDependencies) -> None:
        self.settings = settings
        self.deps = deps

    def _cache_key(
        self, tenant_id: str, modality: Modality, payload: str, model_id: str
    ) -> str:
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"inference:{tenant_id}:{modality}:{model_id}:{digest}"

    def _resolve_model(
        self,
        modality: Modality,
        tenant_id: str,
        model_id: str | None,
        use_ab_test: bool,
        task_hint: str | None = None,
    ) -> ModelRecord:
        return self.deps.registry.resolve(
            modality=modality,
            tenant_id=tenant_id,
            preferred_model_id=model_id,
            use_ab_test=use_ab_test,
            task_hint=task_hint,
        )

    def _payload_hash(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    async def infer_text(
        self,
        text: str,
        tenant_id: str,
        request_id: str | None = None,
        model_id: str | None = None,
        use_ab_test: bool = True,
        question: str | None = None,
        context: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> InferenceResult:
        request_id = request_id or str(uuid.uuid4())
        task_hint = "question-answering" if question and context else "sentiment"
        model = self._resolve_model(
            Modality.text,
            tenant_id,
            model_id,
            use_ab_test,
            task_hint=task_hint,
        )
        resolved_task = infer_model_task(model)
        logger.info(
            "Text inference resolved model_id=%s resolved_task=%s endpoint=%s tenant_id=%s",
            model.model_id,
            resolved_task,
            model.endpoint_name or model.model_id,
            tenant_id,
        )
        cache_key = self._cache_key(
            tenant_id,
            Modality.text,
            self._payload_hash(
                {
                    "text": text,
                    "question": question,
                    "context": context,
                    "metadata": metadata or {},
                }
            ),
            model.model_id,
        )
        cached = await self.deps.cache.get(cache_key)
        if cached:
            CACHE_HIT_RATE.labels("redis").inc()
            cached_value = dict(cached.value)
            cached_value["cached"] = True
            return InferenceResult(**cached_value)

        start = time.perf_counter()
        ACTIVE_REQUESTS.inc()
        try:
            predictions = await asyncio.to_thread(
                self.deps.engine.predict_text,
                model,
                text,
                question,
                context,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            result = InferenceResult(
                request_id=request_id,
                tenant_id=tenant_id,
                model_id=model.model_id,
                modality=Modality.text,
                label=predictions.label,
                confidence=predictions.confidence,
                predictions=predictions.predictions,
                cached=False,
                latency_ms=latency_ms,
            )
            await self.deps.cache.set(cache_key, result.model_dump())
            INFERENCE_LATENCY.labels(model.model_id, Modality.text.value).observe(
                latency_ms / 1000
            )
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            logger.warning(
                "Text inference rejected model_id=%s resolved_task=%s endpoint=%s error=%s",
                model.model_id,
                resolved_task,
                model.endpoint_name or model.model_id,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc
        except Exception as exc:
            logger.exception(
                "Text inference failed model_id=%s resolved_task=%s endpoint=%s",
                model.model_id,
                resolved_task,
                model.endpoint_name or model.model_id,
            )
            raise
        finally:
            ACTIVE_REQUESTS.dec()

    async def infer_image(
        self,
        image_bytes: bytes,
        tenant_id: str,
        request_id: str | None = None,
        model_id: str | None = None,
        use_ab_test: bool = True,
    ) -> InferenceResult:
        request_id = request_id or str(uuid.uuid4())
        model = self._resolve_model(Modality.vision, tenant_id, model_id, use_ab_test)
        resolved_task = infer_model_task(model)
        logger.info(
            "Vision inference resolved model_id=%s resolved_task=%s endpoint=%s tenant_id=%s",
            model.model_id,
            resolved_task,
            model.endpoint_name or model.model_id,
            tenant_id,
        )
        payload_digest = hashlib.sha256(image_bytes).hexdigest()
        cache_key = f"{tenant_id}:{Modality.vision}:{model.model_id}:{payload_digest}"
        cached = await self.deps.cache.get(cache_key)
        if cached:
            CACHE_HIT_RATE.labels("redis").inc()
            cached_value = dict(cached.value)
            cached_value["cached"] = True
            return InferenceResult(**cached_value)

        start = time.perf_counter()
        ACTIVE_REQUESTS.inc()
        try:
            predictions = await asyncio.to_thread(
                self.deps.engine.predict_image,
                model,
                image_bytes,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            result = InferenceResult(
                request_id=request_id,
                tenant_id=tenant_id,
                model_id=model.model_id,
                modality=Modality.vision,
                label=predictions.label,
                confidence=predictions.confidence,
                predictions=predictions.predictions,
                cached=False,
                latency_ms=latency_ms,
            )
            await self.deps.cache.set(cache_key, result.model_dump())
            INFERENCE_LATENCY.labels(model.model_id, Modality.vision.value).observe(
                latency_ms / 1000
            )
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            logger.warning(
                "Vision inference rejected model_id=%s resolved_task=%s endpoint=%s error=%s",
                model.model_id,
                resolved_task,
                model.endpoint_name or model.model_id,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc
        except Exception as exc:
            logger.exception(
                "Vision inference failed model_id=%s resolved_task=%s endpoint=%s",
                model.model_id,
                resolved_task,
                model.endpoint_name or model.model_id,
            )
            raise
        finally:
            ACTIVE_REQUESTS.dec()

    async def batch_infer(
        self,
        items: list[BatchInferenceItem],
        tenant_id: str,
        request_id: str | None = None,
    ) -> list[InferenceResult]:
        request_id = request_id or str(uuid.uuid4())
        tasks = [self._infer_item(item, tenant_id, request_id) for item in items]
        return await asyncio.gather(*tasks)

    async def _infer_item(
        self, item: BatchInferenceItem, tenant_id: str, request_id: str
    ) -> InferenceResult:
        if item.modality == Modality.text:
            return await self.infer_text(
                item.text or "",
                tenant_id=tenant_id,
                request_id=request_id,
                model_id=item.model_id,
                use_ab_test=item.use_ab_test,
                question=getattr(item, "question", None),
                context=getattr(item, "context", None),
                metadata=item.metadata,
            )
        if item.modality == Modality.vision:
            image_bytes = base64.b64decode(item.image_base64 or "")
            return await self.infer_image(
                image_bytes,
                tenant_id=tenant_id,
                request_id=request_id,
                model_id=item.model_id,
                use_ab_test=item.use_ab_test,
            )
        raise ValueError(f"Unsupported modality: {item.modality}")
