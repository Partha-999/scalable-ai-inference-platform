from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis

from app.core.config import Settings


@dataclass(slots=True)
class CacheValue:
    value: Any
    cached: bool


class RedisCache:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Redis | None = None
        self._memory_cache: dict[str, str] = {}

    async def client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
        return self._client

    async def get(self, key: str) -> CacheValue | None:
        try:
            client = await self.client()
            payload = await client.get(key)
        except Exception:
            payload = self._memory_cache.get(key)
        if payload is None:
            return None
        return CacheValue(value=json.loads(payload), cached=True)

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps(value, default=str)
        ttl = ttl_seconds or self.settings.redis_cache_ttl_seconds
        try:
            client = await self.client()
            await client.set(key, payload, ex=ttl)
        except Exception:
            self._memory_cache[key] = payload

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
