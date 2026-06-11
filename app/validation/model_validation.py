from __future__ import annotations

import asyncio
import base64
import json
import statistics
import time
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

import httpx
from fastapi import FastAPI
from pydantic import ValidationError

from app.core.config import get_settings
from app.models.domain import ModelRecord, Modality
from app.schemas.inference import PredictionResponse
from app.services.model_registry import ModelRegistry, infer_model_task

SENTIMENT_TEXT = "I love this product"
NER_TEXT = "Barack Obama visited Paris"
QA_QUESTION = "What is the capital of France?"
QA_CONTEXT = "Paris is the capital and most populous city of France."
VISION_SAMPLE_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAKUlEQVR4nO3NMQEAAAjDMMC/52ECvlRA00nqs3m9AwAAAAAAAAAAgMMWx/EDPS4YA2MAAAAASUVORK5CYII="
OCR_SAMPLE_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAGQAAAAeCAIAAABVOSykAAABoElEQVR4nO3YPYrCQBTA8YlZdLqklzRai42dOH5gMeQIaucx0mvnIVIHLPUAFuIJtFBQGJlOLQXxbREIiytMHuuuG3i/aiATHf7Rh2gBACPp5N59gCyhWAgUC4FiIVAsBIqFQLEQKBYCxUKgWAgUC8Ecy3XdNC+UbEu5P4vok4WQKlYQBM1ms1KpTKdTxtjpdBoMBt1uVwixWq2e3qK19n1fCOH7vtb6lUd+IzDhnE8mEwDYbDae5wHAcDhcLpcAsN/vq9VqvM1xnK+LXq8XhiEAhGHY7/eN75IJFpj+z+Kca63jSeQ4zuVy8TyvXC7HV5VS6/Xatm3Xdc/nM2MsXhSLxd1uVygUrtdrqVRSSv3uM/8TH8Yd+Xw+mdmWZTHGbrfbfD7nnN/v98ViYdv297uMzyCLzDMrl3vcU6/X4+E1m83G4/HTu9rtdhRFjLEoilqt1k+P+U8Yv6jJMErWh8NBSimE6HQ62+02vlSr1UajUbJQSkkpG42GlPJ4PL5+fryDeWaRBP3OQqBYCBQLgWIhUCwEioVAsRAoFgLFQvgE1Px0x0QjVRkAAAAASUVORK5CYII="
SUPPORTED_VALIDATION_TASKS = {
    "sentiment",
    "topic",
    "intent",
    "question-answering",
    "token-classification",
    "text-classification",
    "image-classification",
    "zero-shot-classification",
    "object-detection",
    "ocr",
}


from enum import Enum

class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_TESTED = "NOT_TESTED"


@dataclass(slots=True)
class ModelValidationResult:
    model_id: str
    modality: str
    task: str
    endpoint_name: str | None
    status: ValidationStatus
    success: bool
    status_code: int | None = None
    cached: bool | None = None
    latency_ms: float | None = None
    confidence: float | None = None
    label: str | None = None
    error: str | None = None
    error_category: str | None = None
    response: dict[str, Any] | None = None


@dataclass(slots=True)
class ValidationReport:
    source: str
    tenant_id: str
    total_models: int
    passed: int
    failed: int
    not_tested: int
    results: list[ModelValidationResult] = field(default_factory=list)

    @property
    def failed_models(self) -> list[str]:
        return [result.model_id for result in self.results if result.status == ValidationStatus.FAILED]

    @property
    def not_tested_models(self) -> list[str]:
        return [result.model_id for result in self.results if result.status == ValidationStatus.NOT_TESTED]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "tenant_id": self.tenant_id,
            "total_models": self.total_models,
            "passed": self.passed,
            "failed": self.failed,
            "not_tested": self.not_tested,
            "failed_models": self.failed_models,
            "not_tested_models": self.not_tested_models,
            "results": [asdict(result) for result in self.results],
        }

    def write_json(self, path: Path) -> Path:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, default=str), encoding="utf-8"
        )
        return path

    def to_markdown(self) -> str:
        passed_latencies = [
            r.latency_ms for r in self.results if r.status == ValidationStatus.PASSED and r.latency_ms is not None
        ]
        avg_latency_str = (
            f"{int(statistics.mean(passed_latencies))}ms"
            if passed_latencies
            else "N/A"
        )

        md = []
        md.append("# MODEL VALIDATION REPORT\n")
        md.append(f"Total Models: {self.total_models}\n")
        md.append(f"PASSED: {self.passed}")
        md.append(f"FAILED: {self.failed}")
        md.append(f"NOT TESTED: {self.not_tested}\n")

        # Passed section
        md.append("## Passed Models\n")
        for r in self.results:
            if r.status == ValidationStatus.PASSED:
                md.append(f"✓ {r.model_id}")
        md.append("")

        # Failed section
        md.append("## Failed Models\n")
        failed_results = [r for r in self.results if r.status == ValidationStatus.FAILED]
        if not failed_results:
            md.append("*No failed models.*")
        else:
            for r in failed_results:
                md.append(f"✗ {r.model_id}")
                md.append("  Reason:")
                reason = r.error or "Unknown failure"
                for line in reason.split("\n"):
                    md.append(f"  {line}")
                md.append("")
        md.append("")

        # Not Tested section
        md.append("## Not Tested Models\n")
        not_tested_results = [r for r in self.results if r.status == ValidationStatus.NOT_TESTED]
        if not not_tested_results:
            md.append("*No untested models.*")
        else:
            for r in not_tested_results:
                md.append(f"✗ {r.model_id}")
                md.append("  Reason:")
                reason = r.error or "Unknown failure / not executed"
                for line in reason.split("\n"):
                    md.append(f"  {line}")
                md.append("")
        md.append("")

        md.append("## Summary Table\n")
        md.append("| Model Name | HF Model | Task | Status | Latency | Error Category | Error Message |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in self.results:
            lat_val = (
                f"{r.latency_ms:.2f}"
                if (r.status == ValidationStatus.PASSED and r.latency_ms is not None)
                else "-"
            )
            hf_model = r.endpoint_name or "-"
            err_cat = r.error_category or "-"
            err_msg = r.error if r.error else "-"
            md.append(
                f"| {r.model_id} | {hf_model} | {r.task} | {r.status} | {lat_val} | {err_cat} | {err_msg} |"
            )

        md.append(f"\nAverage Latency:\n  {avg_latency_str}")
        return "\n".join(md)

    def write_markdown(self, path: Path) -> Path:
        path.write_text(self.to_markdown(), encoding="utf-8")
        return path


class ValidationTransportClient:
    def __init__(self, app: FastAPI) -> None:
        self.app = app

    async def __aenter__(self) -> httpx.AsyncClient:
        self.client = httpx.AsyncClient(
            app=self.app,
            base_url="http://testserver",
            timeout=httpx.Timeout(60.0),
        )
        return self.client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.client.aclose()


def discover_models_from_registry(
    registry_path: Path | None = None,
) -> list[ModelRecord]:
    settings = get_settings()
    path = registry_path or settings.model_registry_path
    return ModelRegistry.load(path).list_models()


async def discover_models_from_endpoint(
    client: httpx.AsyncClient, token: str, tenant_id: str
) -> list[ModelRecord]:
    response = await client.get(
        "/api/v1/inference/models",
        headers=_auth_headers(token, tenant_id),
    )
    response.raise_for_status()
    payload = response.json()
    return [ModelRecord(**item) for item in payload.get("models", [])]


def validation_payload_for_model(model: ModelRecord) -> dict[str, Any]:
    task = infer_model_task(model)
    if model.modality == Modality.vision:
        img_b64 = OCR_SAMPLE_IMAGE if task == "ocr" else VISION_SAMPLE_IMAGE
        return {
            "image_base64": img_b64,
            "model_id": model.model_id,
            "use_ab_test": False,
        }

    if task == "question-answering":
        return {
            "question": QA_QUESTION,
            "context": QA_CONTEXT,
            "model_id": model.model_id,
            "use_ab_test": False,
        }

    if task == "token-classification":
        return {
            "text": NER_TEXT,
            "model_id": model.model_id,
            "use_ab_test": False,
        }

    if task in {
        "sentiment",
        "topic",
        "intent",
        "text-classification",
        "zero-shot-classification",
    }:
        return {
            "text": SENTIMENT_TEXT,
            "model_id": model.model_id,
            "use_ab_test": False,
        }

    return {
        "text": SENTIMENT_TEXT,
        "model_id": model.model_id,
        "use_ab_test": False,
    }


async def run_validation_suite(
    app: FastAPI,
    tenant_id: str,
    registry_path: Path | None = None,
    discovery_source: str = "registry",
    subject: str = "validation-runner",
    write_report_to: Path | None = None,
    write_markdown_to: Path | None = None,
) -> ValidationReport:
    # Conditionally execute the FastAPI lifespan start/stop handlers if the
    # app is not already preconfigured (such as during unit testing with custom app mocks).
    lifespan_ctx = (
        app.router.lifespan_context(app)
        if getattr(app.state, "inference_service", None) is None
        else nullcontext()
    )
    async with lifespan_ctx:
        async with ValidationTransportClient(app) as client:
            token = await _issue_token(client, subject, tenant_id)
            models = (
                discover_models_from_registry(registry_path)
                if discovery_source == "registry"
                else await discover_models_from_endpoint(client, token, tenant_id)
            )
            results: list[ModelValidationResult] = []
            for model in models:
                res = await _validate_model(client, token, tenant_id, model)
                results.append(res)
                try:
                    from app.services.model_loader import ModelLoader
                    ModelLoader().clear_cache()
                except Exception:
                    pass

            report = ValidationReport(
                source=discovery_source,
                tenant_id=tenant_id,
                total_models=len(models),
                passed=sum(1 for result in results if result.status == ValidationStatus.PASSED),
                failed=sum(1 for result in results if result.status == ValidationStatus.FAILED),
                not_tested=sum(1 for result in results if result.status == ValidationStatus.NOT_TESTED),
                results=results,
            )
            if write_report_to is not None:
                report.write_json(write_report_to)
            if write_markdown_to is not None:
                report.write_markdown(write_markdown_to)
            return report


async def run_concurrent_smoke_test(
    app: FastAPI,
    tenant_id: str,
    payload: dict[str, Any],
    path: str = "/api/v1/inference/text",
    total_requests: int = 100,
    concurrency: int = 25,
    subject: str = "validation-runner",
    tenant_id_factory: Callable[[int], str] | None = None,
    subject_factory: Callable[[int], str] | None = None,
) -> dict[str, Any]:
    async with ValidationTransportClient(app) as client:
        token = await _issue_token(client, subject, tenant_id)
        sem = asyncio.Semaphore(concurrency)
        timings: list[float] = []
        statuses: list[int] = []

        async def invoke(index: int) -> None:
            async with sem:
                request_tenant_id = (
                    tenant_id_factory(index) if tenant_id_factory else tenant_id
                )
                request_subject = (
                    subject_factory(index) if subject_factory else subject
                )
                request_token = token
                if tenant_id_factory is not None or subject_factory is not None:
                    request_token = await _issue_token(
                        client,
                        request_subject,
                        request_tenant_id,
                    )
                request_headers = _auth_headers(request_token, request_tenant_id)
                started = time.perf_counter()
                response = await client.post(
                    path, headers=request_headers, json=payload
                )
                timings.append((time.perf_counter() - started) * 1000)
                statuses.append(response.status_code)

        started_at = time.perf_counter()
        await asyncio.gather(*(invoke(index) for index in range(total_requests)))
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        return {
            "total_requests": total_requests,
            "concurrency": concurrency,
            "success": sum(1 for status_code in statuses if status_code == 200),
            "failures": sum(1 for status_code in statuses if status_code != 200),
            "throughput_rps": (
                total_requests / (elapsed_ms / 1000) if elapsed_ms else 0.0
            ),
            "latency_ms_avg": statistics.mean(timings) if timings else 0.0,
            "latency_ms_p95": _p95(timings),
        }


async def _issue_token(
    client: httpx.AsyncClient, subject: str, tenant_id: str
) -> str:
    response = await client.post(
        "/api/v1/auth/token",
        headers={"X-Tenant-ID": tenant_id},
        json={"subject": subject, "tenant_id": tenant_id, "scopes": ["inference"]},
    )
    response.raise_for_status()
    payload = response.json()
    return payload["access_token"]


def classify_error(err_msg: str, error_class: str | None = None) -> tuple[ValidationStatus, str]:
    err_msg_lower = err_msg.lower()
    
    # Check if the error indicates missing local cache, connection failure, offline mode, or socket block
    not_tested_indicators = [
        "localentrynotfounderror",
        "modelartifactsmissingerror",
        "model weights file not found",
        "model artifacts missing",
        "couldn't connect to 'https://huggingface.co'",
        "cannot find the requested files in the disk cache",
        "winerror 10013",
        "offline mode",
        "local_files_only",
        "connecterror",
        "connecttimeout",
        "connection aborted",
        "unsupported task mapping",
    ]
    
    if error_class == "ModelArtifactsMissingError" or any(ind in err_msg_lower for ind in not_tested_indicators):
        category = "Missing Local Cache / Offline Mode / Network Failure"
        if "winerror 10013" in err_msg_lower or "socket" in err_msg_lower:
            category = "Environment Prevented Execution"
        elif "connect" in err_msg_lower or "net" in err_msg_lower:
            category = "HuggingFace Download / Network Failure"
        elif "unsupported task" in err_msg_lower:
            category = "Unsupported Task Mapping"
        return ValidationStatus.NOT_TESTED, category

    # Otherwise it is FAILED
    if "out of memory" in err_msg_lower or "cuda" in err_msg_lower:
        return ValidationStatus.FAILED, "CUDA Out of Memory"
    if "timeout" in err_msg_lower:
        return ValidationStatus.FAILED, "Inference Timeout"
    if "invalid response schema" in err_msg_lower or "validationerror" in err_msg_lower:
        return ValidationStatus.FAILED, "Schema Validation Error"
    if "missing" in err_msg_lower or "empty" in err_msg_lower or "invalid confidence" in err_msg_lower:
        return ValidationStatus.FAILED, "Value Validation Error"
    
    return ValidationStatus.FAILED, "Runtime / Inference Error"


async def _validate_model(
    client: httpx.AsyncClient, token: str, tenant_id: str, model: ModelRecord
) -> ModelValidationResult:
    task = infer_model_task(model)
    if task not in SUPPORTED_VALIDATION_TASKS:
        return ModelValidationResult(
            model_id=model.model_id,
            modality=model.modality.value,
            task=task,
            endpoint_name=model.endpoint_name,
            status=ValidationStatus.NOT_TESTED,
            success=False,
            error="Unsupported task mapping",
            error_category="Unsupported Task Mapping",
        )

    path = (
        "/api/v1/inference/vision"
        if model.modality == Modality.vision
        else "/api/v1/inference/text"
    )
    payload = validation_payload_for_model(model)
    headers = _auth_headers(token, tenant_id)

    try:
        started = time.perf_counter()
        response = await client.post(
            path, headers=headers, json=payload, timeout=50.0
        )
        latency = (time.perf_counter() - started) * 1000

        # Handle API Error Codes
        if response.status_code != 200:
            error_class = None
            try:
                payload_json = response.json()
                err_detail = payload_json.get("detail", response.text)
                error_class = payload_json.get("error_class")
            except Exception:
                err_detail = response.text
            
            if error_class == "ModelArtifactsMissingError":
                from app.core.exceptions import ModelArtifactsMissingError
                raise ModelArtifactsMissingError(err_detail)

            raise ValueError(f"HTTP {response.status_code}: {err_detail}")

        # Schema & Response Validation
        try:
            payload_data = _parse_prediction_response(response)
        except ValidationError as e:
            raise ValueError(f"invalid response schema: {str(e)}")

        # Task-Specific Assertions
        if task in {"sentiment", "text-classification", "topic", "intent"}:
            if not payload_data.label:
                raise ValueError("Response missing prediction label")
            if (
                payload_data.confidence is None
                or not (0.0 <= payload_data.confidence <= 1.0)
            ):
                raise ValueError("Response missing or invalid confidence score")

        elif task == "question-answering":
            if not payload_data.label:  # label holds the answer text
                raise ValueError("Response missing QA answer text")
            if (
                payload_data.confidence is None
                or not (0.0 <= payload_data.confidence <= 1.0)
            ):
                raise ValueError("Response missing or invalid confidence score")

        elif task == "token-classification":
            if not payload_data.predictions:
                raise ValueError("Response predictions list is empty")
            for idx, entity in enumerate(payload_data.predictions):
                if "score" not in entity:
                    raise ValueError(
                        f"Prediction entity index {idx} missing score"
                    )

        elif task == "image-classification":
            if not payload_data.label:
                raise ValueError("Response missing classification label")
            if (
                payload_data.confidence is None
                or not (0.0 <= payload_data.confidence <= 1.0)
            ):
                raise ValueError("Response missing or invalid confidence score")

        elif task == "zero-shot-classification":
            if not payload_data.predictions:
                raise ValueError("Response predictions list is empty")
            for idx, label_score in enumerate(payload_data.predictions):
                if "score" not in label_score or "label" not in label_score:
                    raise ValueError(
                        f"Prediction item index {idx} missing label or score"
                    )

        elif task == "object-detection":
            for idx, pred in enumerate(payload_data.predictions):
                if "score" not in pred or "label" not in pred:
                    raise ValueError(
                        f"Prediction item index {idx} missing label or score"
                    )
                if "box" not in pred:
                    raise ValueError(
                        f"Prediction item index {idx} missing bounding box (box)"
                    )

        elif task == "ocr":
            if not payload_data.predictions:
                raise ValueError("Response predictions list is empty")
            ocr_pred = payload_data.predictions[0]
            if "text" not in ocr_pred or not ocr_pred["text"]:
                raise ValueError("OCR response missing extracted text")
            if "score" not in ocr_pred or ocr_pred["score"] is None:
                raise ValueError("OCR response missing confidence score")
            if "words" not in ocr_pred or not isinstance(ocr_pred["words"], list):
                raise ValueError("OCR response missing words list")
            if len(ocr_pred["words"]) == 0:
                raise ValueError("OCR response word list is empty")
            for idx, word_data in enumerate(ocr_pred["words"]):
                if "text" not in word_data or not word_data["text"]:
                    raise ValueError(f"OCR word at index {idx} missing text")
                if "bbox" not in word_data or not isinstance(word_data["bbox"], list) or len(word_data["bbox"]) != 4:
                    raise ValueError(f"OCR word at index {idx} missing or invalid bbox")
                if "confidence" not in word_data or not isinstance(word_data["confidence"], (int, float)):
                    raise ValueError(f"OCR word at index {idx} missing or invalid confidence")

        return ModelValidationResult(
            model_id=model.model_id,
            modality=model.modality.value,
            task=task,
            endpoint_name=model.endpoint_name,
            status=ValidationStatus.PASSED,
            success=True,
            status_code=response.status_code,
            cached=payload_data.cached,
            latency_ms=latency,
            confidence=payload_data.confidence,
            label=payload_data.label,
            error=None,
            error_category=None,
            response=payload_data.model_dump(),
        )

    except Exception as exc:
        err_msg = str(exc)
        error_class = exc.__class__.__name__

        status_val, category = classify_error(err_msg, error_class)

        return ModelValidationResult(
            model_id=model.model_id,
            modality=model.modality.value,
            task=task,
            endpoint_name=model.endpoint_name,
            status=status_val,
            success=(status_val == ValidationStatus.PASSED),
            error=err_msg,
            error_category=category,
            response=None,
        )


def _parse_prediction_response(response: httpx.Response) -> PredictionResponse:
    payload = response.json()
    return PredictionResponse.model_validate(payload)


def _auth_headers(token: str, tenant_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
    }


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) < 20:
        return max(values)
    return statistics.quantiles(values, n=20)[18]


if __name__ == "__main__":
    import argparse
    import sys
    from app.main import create_app

    # Reconfigure stdout to use UTF-8 to prevent charmap encoding errors on Windows terminal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Model Certification Suite")
    parser.add_argument(
        "--discovery",
        choices=["registry", "endpoint"],
        default="registry",
        help="Source to discover models from",
    )
    parser.add_argument(
        "--registry-path",
        type=str,
        default=None,
        help="Path to custom model registry json config",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="validation-report.json",
        help="Path to save the JSON report",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="validation-report.md",
        help="Path to save the Markdown report",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default="tenant-a",
        help="Tenant ID for authentication",
    )
    args = parser.parse_args()

    app_instance = create_app()
    reg_path = Path(args.registry_path) if args.registry_path else None
    json_path = Path(args.output_json) if args.output_json else None
    md_path = Path(args.output_md) if args.output_md else None

    async def main_run() -> int:
        print("Starting Model Certification Suite...")
        report = await run_validation_suite(
            app=app_instance,
            tenant_id=args.tenant_id,
            registry_path=reg_path,
            discovery_source=args.discovery,
            write_report_to=json_path,
            write_markdown_to=md_path,
        )
        print("\n" + report.to_markdown())
        return report.failed

    failed_count = asyncio.run(main_run())
    if failed_count > 0:
        print(f"\nCertification FAILED: {failed_count} model(s) failed.")
        sys.exit(1)
    else:
        print("\nCertification PASSED: All models successfully verified.")
        sys.exit(0)
