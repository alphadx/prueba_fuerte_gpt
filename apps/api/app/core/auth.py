"""Authentication helpers for API endpoints.

MVP approach:
- Tokens are expected as JWT-like bearer strings coming from an external IdP.
- Signature verification is intentionally out of scope for this repo stage.
- Claims extraction powers role-based authorization inside the API.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    """Identity context extracted from an access token."""

    subject: str
    roles: frozenset[str]


def _decode_payload(token: str) -> dict[str, object]:
    """Decode JWT payload segment without signature verification.

    This keeps the API decoupled from a specific IdP SDK while step 5 focuses on
    modular authorization wiring.
    """
    try:
        segments = token.split(".")
        if len(segments) != 3:
            raise ValueError("token format")

        payload_segment = segments[1]
        padding = "=" * (-len(payload_segment) % 4)
        decoded = base64.urlsafe_b64decode(f"{payload_segment}{padding}".encode("utf-8"))
        payload = json.loads(decoded.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    return payload


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    """Extract identity and roles from Bearer token claims."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = _decode_payload(credentials.credentials)
    subject = payload.get("sub")
    roles_claim = payload.get("roles", [])

    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail="Missing token subject")

    if not isinstance(roles_claim, list) or not all(isinstance(role, str) for role in roles_claim):
        raise HTTPException(status_code=401, detail="Invalid roles claim")

    return AuthContext(subject=subject, roles=frozenset(roles_claim))
