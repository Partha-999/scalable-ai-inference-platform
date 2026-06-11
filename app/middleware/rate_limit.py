from __future__ import annotations

import time

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from redis.asyncio import Redis

from app.core.config import Settings
from app.monitoring.metrics import RATE_LIMIT_REJECTIONS


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self._buckets: dict[str, list[float]] = {}
        self._client: Redis | None = None

    async def _redis_client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                db=self.settings.redis_rate_limit_db,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
        return self._client

    async def _allow_with_redis(self, tenant_id: str) -> bool:
        client = await self._redis_client()
        window = int(time.time() / self.settings.rate_limit_window_seconds)
        key = f"rate-limit:{tenant_id}:{window}"
        current = await client.incr(key)
        if current == 1:
            await client.expire(key, self.settings.rate_limit_window_seconds + 1)
        return current <= self.settings.rate_limit_requests

    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = request.headers.get("X-Tenant-ID", "anonymous")
        allowed = True
        try:
            allowed = await self._allow_with_redis(tenant_id)
        except Exception:
            now = time.time()
            window_start = now - self.settings.rate_limit_window_seconds
            bucket = [
                timestamp
                for timestamp in self._buckets.get(tenant_id, [])
                if timestamp >= window_start
            ]
            allowed = len(bucket) < self.settings.rate_limit_requests
            if allowed:
                bucket.append(now)
                self._buckets[tenant_id] = bucket

        if not allowed:
            RATE_LIMIT_REJECTIONS.labels(tenant_id).inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        return await call_next(request)
