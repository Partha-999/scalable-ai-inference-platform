from __future__ import annotations

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    subject: str
    tenant_id: str
    scopes: list[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
