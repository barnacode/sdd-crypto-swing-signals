"""JWT scope auth for the dashboard (T023).

Two-scheme posture (FR-027): API key for services/AI (deps.py); JWT with ``read``/``admin``
scopes for the dashboard. Used by US5/US6 endpoints (e.g. admin-only backtests).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import jwt
from fastapi import Header, HTTPException, Request, status


def encode_jwt(scopes: list[str], secret: str) -> str:
    return jwt.encode({"scopes": scopes}, secret, algorithm="HS256")


def _decode(token: str, secret: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:  # invalid/expired token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from exc


def require_scope(scope: str) -> Callable[..., Awaitable[None]]:
    """Dependency factory: require a JWT bearing ``scope`` in its scopes claim."""

    async def _dep(request: Request, authorization: str | None = Header(default=None)) -> None:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
            )
        secret: str = request.app.state.settings.jwt_secret
        claims = _decode(authorization.removeprefix("Bearer "), secret)
        if scope not in claims.get("scopes", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"missing scope: {scope}"
            )

    return _dep
