import base64
import hashlib
import hmac
import json
import os
import time

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import get_auth_context


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _build_token(payload: dict, *, alg: str = "none", secret: str | None = None) -> str:
    header = {"alg": alg, "typ": "JWT"}
    header_raw = _b64url(json.dumps(header).encode())
    payload_raw = _b64url(json.dumps(payload).encode())
    signing_input = f"{header_raw}.{payload_raw}"

    if alg == "HS256" and secret:
        signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        return f"{signing_input}.{_b64url(signature)}"

    return f"{signing_input}.sig"


def test_auth_accepts_roles_claim_without_secret() -> None:
    os.environ.pop("JWT_HS256_SECRET", None)
    token = _build_token({"sub": "u-1", "roles": ["admin"]})

    auth = get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert auth.subject == "u-1"
    assert auth.roles == frozenset({"admin"})


def test_auth_accepts_keycloak_realm_roles() -> None:
    os.environ.pop("JWT_HS256_SECRET", None)
    token = _build_token({"sub": "u-2", "realm_access": {"roles": ["bodega"]}})

    auth = get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert auth.roles == frozenset({"bodega"})


def test_auth_rejects_expired_token() -> None:
    os.environ.pop("JWT_HS256_SECRET", None)
    token = _build_token({"sub": "u-3", "roles": ["admin"], "exp": int(time.time()) - 10})

    with pytest.raises(HTTPException) as exc:
        get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Expired token"


def test_auth_enforces_hs256_signature_when_secret_is_set() -> None:
    os.environ["JWT_HS256_SECRET"] = "test-secret"
    token = _build_token({"sub": "u-4", "roles": ["admin"]}, alg="HS256", secret="test-secret")

    auth = get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert auth.subject == "u-4"
    os.environ.pop("JWT_HS256_SECRET", None)


def test_auth_rejects_bad_signature() -> None:
    os.environ["JWT_HS256_SECRET"] = "test-secret"
    token = _build_token({"sub": "u-5", "roles": ["admin"]}, alg="HS256", secret="wrong-secret")

    with pytest.raises(HTTPException) as exc:
        get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token signature"
    os.environ.pop("JWT_HS256_SECRET", None)
