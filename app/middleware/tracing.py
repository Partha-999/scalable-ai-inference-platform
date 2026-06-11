from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import TENANT_ID, TRACE_ID


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        tenant_id = request.headers.get("X-Tenant-ID", "anonymous")
        trace_token = TRACE_ID.set(trace_id)
        tenant_token = TENANT_ID.set(tenant_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = trace_id
            return response
        finally:
            TRACE_ID.reset(trace_token)
            TENANT_ID.reset(tenant_token)
