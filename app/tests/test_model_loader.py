from __future__ import annotations

from app.models.domain import Modality, ModelRecord
from app.services.model_loader import LoadedPipeline, ModelLoader
from app.services.model_registry import infer_model_task


def test_infer_model_task_maps_semantic_text_tasks():
    registry_cases = {
        "text-sentiment-v1": "sentiment",
        "text-topic-v1": "topic",
        "text-intent-v1": "intent",
        "text-qa-v1": "question-answering",
        "text-entity-v1": "token-classification",
        "text-classify-v1": "text-classification",
    }

    for model_id, expected_task in registry_cases.items():
        model = ModelRecord(
            model_id=model_id,
            modality=Modality.text,
            framework="transformers",
            version="1.0.0",
        )
        assert infer_model_task(model) == expected_task


def test_model_loader_caches_and_normalizes_qa(monkeypatch):
    ModelLoader._instance = None
    loader = ModelLoader()
    calls: list[str] = []

    def fake_load_pipeline(self, model):
        calls.append(model.model_id)
        return LoadedPipeline(
            task="question-answering",
            model_name=model.endpoint_name or model.model_id,
            runner=lambda **kwargs: {
                "answer": "Paris",
                "score": 0.99,
                "start": 0,
                "end": 5,
            },
        )

    monkeypatch.setattr(ModelLoader, "_load_pipeline", fake_load_pipeline)

    model = ModelRecord(
        model_id="text-qa-v1",
        modality=Modality.text,
        framework="transformers",
        version="1.0.0",
        endpoint_name="deepset/roberta-base-squad2",
    )

    first = loader.predict_text(
        model,
        question="What is the capital of France?",
        context="Paris is the capital of France.",
    )
    second = loader.predict_text(
        model,
        question="What is the capital of France?",
        context="Paris is the capital of France.",
    )

    assert calls == ["text-qa-v1"]
    assert first[0]["label"] == "Paris"
    assert second[0]["answer"] == "Paris"


def test_model_loader_maps_semantic_task_to_hf_pipeline(monkeypatch):
    ModelLoader._instance = None
    loader = ModelLoader()
    captured = {}

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return lambda *args, **kwargs: [{"label": "positive", "score": 0.99}]

    monkeypatch.setattr("app.services.model_loader.pipeline", fake_pipeline)

    model = ModelRecord(
        model_id="text-sentiment-v1",
        modality=Modality.text,
        framework="transformers",
        version="1.0.0",
        endpoint_name="distilbert-base-uncased-finetuned-sst-2-english",
    )

    loader.get_pipeline(model)

    assert captured["task"] == "text-classification"
    assert captured["model"] == "distilbert-base-uncased-finetuned-sst-2-english"
