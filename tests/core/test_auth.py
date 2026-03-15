import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import get_auth_context


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_HS256_SECRET", raising=False)
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)


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


def test_auth_rejects_unsigned_token_by_default() -> None:
    token = _build_token({"sub": "u-1", "roles": ["admin"]})

    with pytest.raises(HTTPException) as exc:
        get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Token verification requires JWT_HS256_SECRET"


def test_auth_accepts_unsigned_token_only_with_explicit_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_ALLOW_INSECURE_TOKENS", "true")
    token = _build_token({"sub": "u-1", "roles": ["admin"]})

    auth = get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert auth.subject == "u-1"
    assert auth.roles == frozenset({"admin"})


def test_auth_accepts_keycloak_realm_roles_when_insecure_mode_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_ALLOW_INSECURE_TOKENS", "true")
    token = _build_token({"sub": "u-2", "realm_access": {"roles": ["bodega"]}})

    auth = get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert auth.roles == frozenset({"bodega"})


def test_auth_rejects_expired_token() -> None:
    token = _build_token({"sub": "u-3", "roles": ["admin"], "exp": int(time.time()) - 10}, alg="HS256", secret="test-secret")

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("JWT_HS256_SECRET", "test-secret")
        with pytest.raises(HTTPException) as exc:
            get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Expired token"


def test_auth_enforces_hs256_signature_when_secret_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    token = _build_token({"sub": "u-4", "roles": ["admin"]}, alg="HS256", secret="test-secret")

    auth = get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert auth.subject == "u-4"


def test_auth_rejects_bad_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    token = _build_token({"sub": "u-5", "roles": ["admin"]}, alg="HS256", secret="wrong-secret")

    with pytest.raises(HTTPException) as exc:
        get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token signature"


def test_auth_rejects_unexpected_issuer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.setenv("JWT_EXPECTED_ISS", "https://issuer.erp")
    token = _build_token(
        {"sub": "u-6", "roles": ["admin"], "iss": "https://other-issuer"},
        alg="HS256",
        secret="test-secret",
    )

    with pytest.raises(HTTPException) as exc:
        get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token issuer"


def test_auth_accepts_expected_audience_in_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.setenv("JWT_EXPECTED_AUD", "erp-api")
    token = _build_token(
        {"sub": "u-7", "roles": ["admin"], "aud": ["erp-web", "erp-api"]},
        alg="HS256",
        secret="test-secret",
    )

    auth = get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert auth.subject == "u-7"


def test_auth_rejects_invalid_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.setenv("JWT_EXPECTED_AUD", "erp-api")
    token = _build_token(
        {"sub": "u-8", "roles": ["admin"], "aud": "other-aud"},
        alg="HS256",
        secret="test-secret",
    )

    with pytest.raises(HTTPException) as exc:
        get_auth_context(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token audience"
