from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.core.dependencies import get_tenant_id
from app.core.security import get_authenticated_subject
from app.models.domain import Modality
from app.schemas.inference import (
    BatchInferenceRequest,
    BatchInferenceResponse,
    PredictionResponse,
    TextInferenceRequest,
    VisionInferenceRequest,
)
from app.schemas.model import ModelInfo, ModelRegistryResponse
from app.services.inference_service import InferenceService

router = APIRouter()


def _service(request: Request) -> InferenceService:
    service = getattr(request.app.state, "inference_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference service not ready",
        )
    return service


@router.get("/models", response_model=ModelRegistryResponse)
async def list_models(request: Request) -> ModelRegistryResponse:
    service = _service(request)
    models = [
        ModelInfo(**model.model_dump()) for model in service.deps.registry.list_models()
    ]
    return ModelRegistryResponse(models=models)


@router.post("/text", response_model=PredictionResponse)
async def text_inference(
    payload: TextInferenceRequest,
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    auth: dict[str, Any] = Depends(get_authenticated_subject),
) -> PredictionResponse:
    result = await _service(request).infer_text(
        payload.text,
        tenant_id=tenant_id,
        model_id=payload.model_id,
        use_ab_test=payload.use_ab_test,
        question=payload.question,
        context=payload.context,
        metadata=payload.metadata,
    )
    return PredictionResponse(**result.model_dump())


@router.post("/vision", response_model=PredictionResponse)
async def vision_inference(
    payload: VisionInferenceRequest,
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    auth: dict[str, Any] = Depends(get_authenticated_subject),
) -> PredictionResponse:
    image_bytes = base64.b64decode(payload.image_base64)
    result = await _service(request).infer_image(
        image_bytes,
        tenant_id=tenant_id,
        model_id=payload.model_id,
        use_ab_test=payload.use_ab_test,
    )
    return PredictionResponse(**result.model_dump())


@router.post("/vision/upload", response_model=PredictionResponse)
async def vision_upload(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    auth: dict[str, Any] = Depends(get_authenticated_subject),
    file: UploadFile = File(...),
) -> PredictionResponse:
    image_bytes = await file.read()
    result = await _service(request).infer_image(image_bytes, tenant_id=tenant_id)
    return PredictionResponse(**result.model_dump())


@router.post("/batch", response_model=BatchInferenceResponse)
async def batch_inference(
    payload: BatchInferenceRequest,
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    auth: dict[str, Any] = Depends(get_authenticated_subject),
) -> BatchInferenceResponse:
    results = await _service(request).batch_infer(
        payload.items, tenant_id=tenant_id or payload.tenant_id or "anonymous"
    )
    return BatchInferenceResponse(
        request_id=results[0].request_id if results else "-",
        results=[PredictionResponse(**result.model_dump()) for result in results],
    )


@router.get("/validation/report")
async def get_validation_report(
    auth: dict[str, Any] = Depends(get_authenticated_subject),
) -> Any:
    import json
    from pathlib import Path
    report_path = Path("validation-report.json")
    if not report_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation report not found. Run certification suite first.",
        )
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read validation report: {str(e)}",
        )
