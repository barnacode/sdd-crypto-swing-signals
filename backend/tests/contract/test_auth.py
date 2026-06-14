"""JWT scope auth tests (T022/T023, FR-027)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException

from aegis.api.auth import encode_jwt, require_scope


class _Req:
    def __init__(self, secret: str) -> None:
        self.app = FastAPI()
        self.app.state.settings = type("S", (), {"jwt_secret": secret})()


async def _call(dep, request, authorization):
    return await dep(request, authorization=authorization)


async def test_valid_scope_passes():
    secret = "s3cret"
    token = encode_jwt(["read", "admin"], secret)
    await _call(require_scope("admin"), _Req(secret), f"Bearer {token}")  # no exception ⇒ ok


async def test_missing_bearer_rejected():
    dep = require_scope("read")
    with pytest.raises(HTTPException) as exc:
        await _call(dep, _Req("s"), None)
    assert exc.value.status_code == 401


async def test_wrong_scope_forbidden():
    secret = "s"
    token = encode_jwt(["read"], secret)
    dep = require_scope("admin")
    with pytest.raises(HTTPException) as exc:
        await _call(dep, _Req(secret), f"Bearer {token}")
    assert exc.value.status_code == 403


async def test_invalid_token_rejected():
    dep = require_scope("read")
    with pytest.raises(HTTPException) as exc:
        await _call(dep, _Req("right-secret"), "Bearer not-a-jwt")
    assert exc.value.status_code == 401
