import pytest
from unittest.mock import patch
from app.core.exceptions import ModelArtifactsMissingError
from app.models.domain import ModelRecord, Modality
from app.services.model_loader import ModelLoader
from app.validation.model_validation import (
    classify_error,
    ValidationStatus,
    _validate_model,
)
import httpx


def test_model_loader_raises_model_artifacts_missing_error():
    """Verify that ModelLoader._load_pipeline catches AttributeError from pipeline and raises ModelArtifactsMissingError."""
    loader = ModelLoader()
    model = ModelRecord(
        model_id="test-entity-v1",
        modality=Modality.text,
        framework="transformers",
        version="1.0.0",
        enabled=True,
        ab_group="control",
        endpoint_name="dslim/bert-base-NER",
        description="test"
    )

    with patch("app.services.model_loader.pipeline") as mock_pipeline:
        mock_pipeline.side_effect = AttributeError("'NoneType' object has no attribute 'endswith'")
        with pytest.raises(ModelArtifactsMissingError) as exc_info:
            loader._load_pipeline(model)
        
        assert "Model weights file not found in local cache" in str(exc_info.value)


def test_classify_error_rules():
    """Verify error classification rules map cleanly to FAILED or NOT_TESTED."""
    # NOT_TESTED cases
    status, cat = classify_error("Model weights file not found", "ModelArtifactsMissingError")
    assert status == ValidationStatus.NOT_TESTED
    assert "Missing Local Cache" in cat

    status, cat = classify_error("We couldn't connect to 'https://huggingface.co' to load this file")
    assert status == ValidationStatus.NOT_TESTED
    assert "HuggingFace Download / Network Failure" in cat

    status, cat = classify_error("Failed to establish a new connection: [WinError 10013]")
    assert status == ValidationStatus.NOT_TESTED
    assert "Environment Prevented Execution" in cat

    status, cat = classify_error("Unsupported task mapping")
    assert status == ValidationStatus.NOT_TESTED
    assert "Unsupported Task Mapping" in cat

    # FAILED cases
    status, cat = classify_error("CUDA out of memory error occurred")
    assert status == ValidationStatus.FAILED
    assert "CUDA Out of Memory" in cat

    status, cat = classify_error("invalid response schema: field missing")
    assert status == ValidationStatus.FAILED
    assert "Schema Validation Error" in cat

    status, cat = classify_error("Response missing prediction label")
    assert status == ValidationStatus.FAILED
    assert "Value Validation Error" in cat


@pytest.mark.asyncio
async def test_validate_model_handles_artifacts_missing_gracefully():
    """Verify that _validate_model correctly handles ModelArtifactsMissingError returning status NOT_TESTED."""
    model = ModelRecord(
        model_id="text-entity-v1",
        modality=Modality.text,
        framework="transformers",
        version="1.0.0",
        enabled=True,
        ab_group="control",
        endpoint_name="dslim/bert-base-NER",
        description="test"
    )

    mock_response = httpx.Response(
        status_code=503,
        json={
            "detail": "Model weights file not found",
            "error_class": "ModelArtifactsMissingError"
        }
    )

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        async with httpx.AsyncClient() as client:
            res = await _validate_model(client, token="test_token", tenant_id="tenant-a", model=model)
            assert res.status == ValidationStatus.NOT_TESTED
            assert res.success is False
            assert "Model weights file not found" in res.error
            assert "Missing Local Cache" in res.error_category


def test_infer_model_task_detection():
    """Verify that infer_model_task maps vision models with 'detect' or 'detr' to 'object-detection'."""
    from app.services.model_registry import infer_model_task
    
    model_detr = ModelRecord(
        model_id="vision-detect-v1",
        modality=Modality.vision,
        framework="tensorflow",
        version="1.0.0",
        enabled=True,
        ab_group="control",
        endpoint_name="facebook/detr-resnet-50",
        description="test"
    )
    assert infer_model_task(model_detr) == "object-detection"

    model_vit = ModelRecord(
        model_id="vision-vit-v1",
        modality=Modality.vision,
        framework="tensorflow",
        version="1.0.0",
        enabled=True,
        ab_group="control",
        endpoint_name="google/vit-base-patch16-224",
        description="test"
    )
    assert infer_model_task(model_vit) == "image-classification"


def test_infer_model_task_ocr():
    """Verify that infer_model_task maps vision models with task='ocr' explicitly to 'ocr'."""
    from app.services.model_registry import infer_model_task
    
    model_ocr = ModelRecord(
        model_id="vision-ocr-v1",
        modality=Modality.vision,
        framework="transformers",
        version="1.0.0",
        enabled=True,
        ab_group="control",
        endpoint_name="microsoft/trocr-small-printed",
        task="ocr",
        description="test"
    )
    assert infer_model_task(model_ocr) == "ocr"
