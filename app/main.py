from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.tracing import TracingMiddleware
from app.services.inference_engine import InferenceEngine
from app.services.cache import RedisCache
from app.services.inference_service import InferenceDependencies, InferenceService
from app.services.model_registry import ModelRegistry
from app.services.model_loader import ModelLoader

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    registry = ModelRegistry.load(settings.model_registry_path)
    cache = RedisCache(settings)
    loader = ModelLoader(settings)
    engine = InferenceEngine(loader)
    app.state.settings = settings
    app.state.model_loader = loader
    app.state.inference_service = InferenceService(
        settings,
        InferenceDependencies(
            registry=registry,
            cache=cache,
            engine=engine,
        ),
    )
    logger.info("application_started", extra={"models": len(registry.list_models())})
    try:
        yield
    finally:
        await cache.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.add_middleware(TracingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "trace_id": request.headers.get("X-Request-ID", "-"),
            },
        )

    from app.core.exceptions import ModelArtifactsMissingError

    @app.exception_handler(ModelArtifactsMissingError)
    async def model_artifacts_missing_handler(
        request: Request, exc: ModelArtifactsMissingError
    ) -> JSONResponse:
        logger.error("model_artifacts_missing", extra={"detail": str(exc)})
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Model artifacts missing: {str(exc)}",
                "error_class": "ModelArtifactsMissingError",
                "trace_id": request.headers.get("X-Request-ID", "-"),
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("unhandled_error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Internal Server Error: {str(exc)}",
                "trace_id": request.headers.get("X-Request-ID", "-"),
            },
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
