from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


async def get_tenant_id(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Tenant-ID header is required")
    return x_tenant_id


async def get_request_id(x_request_id: str | None = Header(default=None, alias="X-Request-ID")) -> str:
    return x_request_id or "-"


async def get_settings_dep(settings: Settings = Depends(get_settings)) -> Settings:
    return settings
