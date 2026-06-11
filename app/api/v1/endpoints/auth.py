from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, get_authenticated_subject
from app.schemas.auth import TokenRequest, TokenResponse

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def token(
    payload: TokenRequest, settings: Settings = Depends(get_settings)
) -> TokenResponse:
    token_value = create_access_token(
        payload.subject,
        settings,
        {"tenant_id": payload.tenant_id, "scopes": payload.scopes},
    )
    return TokenResponse(access_token=token_value)


@router.get("/me")
async def me(auth: dict = Depends(get_authenticated_subject)) -> dict:
    return auth
