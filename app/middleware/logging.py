from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            latency = time.perf_counter() - start
            route = request.url.path
            method = request.method
            status = str(getattr(response, "status_code", 500))
            REQUEST_COUNT.labels(route, method, status).inc()
            REQUEST_LATENCY.labels(route, method).observe(latency)
            logger.info(
                "request_complete",
                extra={
                    "route": route,
                    "method": method,
                    "status": status,
                    "latency_ms": latency * 1000,
                },
            )
