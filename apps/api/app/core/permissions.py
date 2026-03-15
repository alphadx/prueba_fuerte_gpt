"""Authorization primitives for domain routes."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException

from app.core.auth import AuthContext, get_auth_context


def require_roles(*allowed_roles: str) -> Callable[[AuthContext], AuthContext]:
    """Build a dependency that enforces any of the provided roles."""

    allowed = frozenset(allowed_roles)

    def _guard(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if auth.roles.isdisjoint(allowed):
            raise HTTPException(status_code=403, detail="Insufficient role permissions")
        return auth

    return _guard
