"""Authentication helpers for API endpoints.

MVP approach:
- Access tokens are expected as JWT bearer strings from an external IdP.
- If `JWT_HS256_SECRET` is configured, HS256 signature verification is enforced.
- Unsigned/unchecked tokens are rejected by default unless `JWT_ALLOW_INSECURE_TOKENS=true`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    """Identity context extracted from an access token."""

    subject: str
    roles: frozenset[str]


def _b64url_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(f"{encoded}{padding}".encode("utf-8"))


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _decode_jwt_parts(token: str) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    try:
        segments = token.split(".")
        if len(segments) != 3:
            raise ValueError("token format")

        header_raw, payload_raw, signature_raw = segments
        header = json.loads(_b64url_decode(header_raw).decode("utf-8"))
        payload = json.loads(_b64url_decode(payload_raw).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from exc

    if not isinstance(header, dict) or not isinstance(payload, dict):
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    return header, payload, f"{header_raw}.{payload_raw}", signature_raw


def _verify_hs256(signing_input: str, signature_raw: str, secret: str) -> None:
    expected = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    actual = _b64url_encode(expected)

    if not hmac.compare_digest(actual, signature_raw):
        raise HTTPException(status_code=401, detail="Invalid token signature")




def _allow_insecure_tokens() -> bool:
    return os.getenv("JWT_ALLOW_INSECURE_TOKENS", "false").lower() == "true"


def _verify_registered_claims(payload: dict[str, Any]) -> None:
    now = int(time.time())

    exp = payload.get("exp")
    if exp is not None:
        if not isinstance(exp, int) or exp <= now:
            raise HTTPException(status_code=401, detail="Expired token")

    nbf = payload.get("nbf")
    if nbf is not None:
        if not isinstance(nbf, int) or nbf > now:
            raise HTTPException(status_code=401, detail="Token not active yet")


def _extract_roles(payload: dict[str, Any]) -> frozenset[str]:
    roles_claim = payload.get("roles")
    if isinstance(roles_claim, list) and all(isinstance(role, str) for role in roles_claim):
        return frozenset(roles_claim)

    # Keycloak-compatible shape
    realm_access = payload.get("realm_access")
    if isinstance(realm_access, dict):
        realm_roles = realm_access.get("roles")
        if isinstance(realm_roles, list) and all(isinstance(role, str) for role in realm_roles):
            return frozenset(realm_roles)

    raise HTTPException(status_code=401, detail="Invalid roles claim")


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    """Extract identity and roles from bearer token claims."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    header, payload, signing_input, signature_raw = _decode_jwt_parts(credentials.credentials)
    secret = os.getenv("JWT_HS256_SECRET")

    algorithm = header.get("alg")
    if secret:
        if algorithm != "HS256":
            raise HTTPException(status_code=401, detail="Unsupported token algorithm")
        _verify_hs256(signing_input, signature_raw, secret)
    elif not _allow_insecure_tokens():
        raise HTTPException(status_code=401, detail="Token verification requires JWT_HS256_SECRET")

    _verify_registered_claims(payload)

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail="Missing token subject")

    roles = _extract_roles(payload)
    return AuthContext(subject=subject, roles=roles)
