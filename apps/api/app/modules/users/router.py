"""Users API router with role-based access control and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.users.schemas import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.modules.users.service import User, user_service

router = APIRouter(prefix="/users", tags=["users"])


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


@router.get("", response_model=UserListResponse)
def list_users(_: AuthContext = Depends(require_roles("admin", "rrhh"))) -> UserListResponse:
    return UserListResponse(items=[_to_response(item) for item in user_service.list_users()])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateRequest, auth: AuthContext = Depends(require_roles("admin"))) -> UserResponse:
    try:
        created = user_service.create_user(
            username=payload.username,
            full_name=payload.full_name,
            role=payload.role,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="users.create", entity=created.id, metadata={"role": created.role})
    return _to_response(created)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, _: AuthContext = Depends(require_roles("admin", "rrhh"))) -> UserResponse:
    try:
        return _to_response(user_service.get_user(user_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    auth: AuthContext = Depends(require_roles("admin")),
) -> UserResponse:
    try:
        updated = user_service.update_user(
            user_id,
            full_name=payload.full_name,
            role=payload.role,
            is_active=payload.is_active,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="users.update", entity=updated.id, metadata={"role": updated.role})
    return _to_response(updated)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_user(user_id: str, auth: AuthContext = Depends(require_roles("admin"))) -> Response:
    try:
        user_service.delete_user(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="users.delete", entity=user_id, metadata={})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
