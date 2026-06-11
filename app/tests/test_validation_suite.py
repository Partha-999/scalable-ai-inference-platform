from __future__ import annotations

import json

import pytest

from app.core.config import get_settings
from app.main import create_app
from app.models.domain import Modality, ModelRecord
from app.services.cache import RedisCache
from app.services.inference_engine import PredictionBundle
from app.services.inference_service import InferenceDependencies, InferenceService
from app.services.model_registry import ModelRegistry, infer_model_task
from app.validation.model_validation import (
    discover_models_from_registry,
    run_concurrent_smoke_test,
    run_validation_suite,
    validation_payload_for_model,
)


class ValidationEngine:
    def predict_text(self, model, text=None, question=None, context=None):
        task = infer_model_task(model)
        prompt = (text or question or "").lower()

        if task == "question-answering":
            return PredictionBundle(
                label="Paris",
                confidence=0.99,
                predictions=[
                    {"label": "Paris", "score": 0.99, "answer": "Paris"},
                ],
            )

        if task == "token-classification":
            return PredictionBundle(
                label="PER",
                confidence=0.97,
                predictions=[
                    {"label": "PER", "score": 0.97, "word": "Barack Obama"},
                    {"label": "LOC", "score": 0.95, "word": "Paris"},
                ],
            )

        if "hate" in prompt or "bad" in prompt:
            return PredictionBundle(
                label="NEGATIVE",
                confidence=0.98,
                predictions=[{"label": "NEGATIVE", "score": 0.98}],
            )

        return PredictionBundle(
            label="POSITIVE",
            confidence=0.98,
            predictions=[{"label": "POSITIVE", "score": 0.98}],
        )

    def predict_image(self, model, image_bytes):
        task = infer_model_task(model)
        if task == "object-detection":
            return PredictionBundle(
                label="cat",
                confidence=0.93,
                predictions=[{"label": "cat", "score": 0.93, "box": {"xmin": 0, "ymin": 0, "xmax": 10, "ymax": 10}}],
            )
        if task == "ocr":
            return PredictionBundle(
                label="OCR_TEXT",
                confidence=0.97,
                predictions=[
                    {
                        "label": "OCR_TEXT",
                        "text": "Hello World",
                        "score": 0.97,
                        "words": [
                            {"text": "Hello", "bbox": [10, 10, 50, 30], "confidence": 0.97},
                            {"text": "World", "bbox": [60, 10, 100, 30], "confidence": 0.97}
                        ]
                    }
                ],
            )
        return PredictionBundle(
            label="object",
            confidence=0.93,
            predictions=[{"label": "object", "score": 0.93}],
        )


@pytest.fixture()
def validation_app():
    app = create_app()
    settings = get_settings()
    registry = ModelRegistry.load(settings.model_registry_path)
    app.state.inference_service = InferenceService(
        settings,
        InferenceDependencies(
            registry=registry,
            cache=RedisCache(settings),
            engine=ValidationEngine(),
        ),
    )
    return app


@pytest.mark.asyncio
async def test_validation_suite_covers_all_registry_models(validation_app, tmp_path):
    settings = get_settings()
    report_path = tmp_path / "validation-report.json"
    markdown_path = tmp_path / "validation-report.md"

    report = await run_validation_suite(
        validation_app,
        tenant_id="tenant-a",
        registry_path=settings.model_registry_path,
        discovery_source="registry",
        write_report_to=report_path,
        write_markdown_to=markdown_path,
    )

    expected_models = discover_models_from_registry(settings.model_registry_path)
    assert report.total_models == len(expected_models)
    assert report.passed == report.total_models
    assert report.failed == 0
    assert {result.model_id for result in report.results} == {
        model.model_id for model in expected_models
    }
    assert all(result.success for result in report.results)
    assert all(result.confidence is not None for result in report.results)
    assert all(
        result.latency_ms is not None and result.latency_ms >= 0
        for result in report.results
    )
    assert all(result.cached is False for result in report.results)

    report_json = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_json["failed"] == 0
    assert len(report_json["results"]) == report.total_models

    report_md = markdown_path.read_text(encoding="utf-8")
    assert "# MODEL VALIDATION REPORT" in report_md
    assert "## Summary Table" in report_md
    assert "Average Latency:" in report_md





@pytest.mark.asyncio
async def test_validation_suite_can_discover_models_from_models_endpoint(
    validation_app,
):
    settings = get_settings()
    expected_models = discover_models_from_registry(settings.model_registry_path)
    report = await run_validation_suite(
        validation_app,
        tenant_id="tenant-a",
        discovery_source="endpoint",
    )

    assert report.total_models == len(expected_models)
    assert report.failed == 0
    assert report.passed == report.total_models


@pytest.mark.asyncio
async def test_parallel_smoke_test_handles_100_requests(validation_app):
    settings = get_settings()
    sentiment_model = next(
        model
        for model in discover_models_from_registry(settings.model_registry_path)
        if model.model_id == "text-sentiment-v1"
    )
    payload = validation_payload_for_model(sentiment_model)

    stats = await run_concurrent_smoke_test(
        validation_app,
        tenant_id="tenant-a",
        payload=payload,
        path="/api/v1/inference/text",
        total_requests=100,
        concurrency=20,
        tenant_id_factory=lambda index: f"tenant-a-{index}",
    )

    assert stats["success"] == 100
    assert stats["failures"] == 0
    assert stats["throughput_rps"] > 0
    assert stats["latency_ms_avg"] > 0
    assert stats["latency_ms_p95"] > 0
