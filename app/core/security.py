from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
logger = logging.getLogger(__name__)


def _token_preview(token: str) -> str:
    # Avoid full token exposure while still giving enough detail for debugging.
    if len(token) <= 16:
        return token
    return f"{token[:8]}...{token[-8:]}"


def create_access_token(
    subject: str, settings: Settings, extra_claims: dict[str, Any] | None = None
) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.access_token_exp_minutes),
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def verify_jwt_token(token: str, settings: Settings) -> dict[str, Any]:
    logger.info(
        "JWT token received token=%s algorithm=%s",
        _token_preview(token),
        settings.jwt_algorithm,
    )
    try:
        claims = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        logger.info("JWT decoded successfully payload=%s", claims)
        return claims
    except ExpiredSignatureError as exc:
        logger.warning("JWT rejected: expired token error=%s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT expired",
        ) from exc
    except InvalidSignatureError as exc:
        logger.warning("JWT rejected: signature mismatch error=%s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT signature mismatch",
        ) from exc
    except DecodeError as exc:
        logger.warning("JWT rejected: decode failure error=%s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT decode failure: {exc}",
        ) from exc
    except InvalidTokenError as exc:
        logger.warning(
            "JWT rejected: invalid token type=%s error=%s",
            type(exc).__name__,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid JWT token: {type(exc).__name__}: {exc}",
        ) from exc


async def get_authenticated_subject(
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    api_key: str | None = Depends(api_key_header),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    if authorization:
        claims = verify_jwt_token(authorization.credentials, settings)
        token_tenant_id = claims.get("tenant_id")
        logger.info(
            "Tenant validation token_tenant_id=%s header_tenant_id=%s",
            token_tenant_id,
            x_tenant_id,
        )
        if x_tenant_id and token_tenant_id and token_tenant_id != x_tenant_id:
            reason = (
                f"Tenant mismatch: token tenant_id={token_tenant_id}, "
                f"header X-Tenant-ID={x_tenant_id}"
            )
            logger.warning("Auth rejected: %s", reason)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=reason,
            )
        return {
            "subject": claims.get("sub", "unknown"),
            "claims": claims,
            "auth_type": "jwt",
        }

    if api_key and api_key in settings.service_api_keys:
        logger.info("API key authenticated")
        return {"subject": api_key, "claims": {"sub": api_key}, "auth_type": "api_key"}

    logger.warning("Auth rejected: missing or invalid credentials")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
    )
