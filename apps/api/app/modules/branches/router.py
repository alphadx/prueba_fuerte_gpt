"""Branches API router with RBAC and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.branches.schemas import BranchCreateRequest, BranchListResponse, BranchResponse, BranchUpdateRequest
from app.modules.branches.service import Branch, branch_service

router = APIRouter(prefix="/branches", tags=["branches"])


def _to_response(branch: Branch) -> BranchResponse:
    return BranchResponse(
        id=branch.id,
        code=branch.code,
        name=branch.name,
        address=branch.address,
        is_active=branch.is_active,
    )


@router.get("", response_model=BranchListResponse)
def list_branches(_: AuthContext = Depends(require_roles("admin", "rrhh", "bodega"))) -> BranchListResponse:
    return BranchListResponse(items=[_to_response(item) for item in branch_service.list_branches()])


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(payload: BranchCreateRequest, auth: AuthContext = Depends(require_roles("admin"))) -> BranchResponse:
    try:
        created = branch_service.create_branch(
            code=payload.code,
            name=payload.name,
            address=payload.address,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="branches.create", entity=created.id, metadata={"code": created.code})
    return _to_response(created)


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(branch_id: str, _: AuthContext = Depends(require_roles("admin", "rrhh", "bodega"))) -> BranchResponse:
    try:
        return _to_response(branch_service.get_branch(branch_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: str,
    payload: BranchUpdateRequest,
    auth: AuthContext = Depends(require_roles("admin")),
) -> BranchResponse:
    try:
        updated = branch_service.update_branch(
            branch_id,
            name=payload.name,
            address=payload.address,
            is_active=payload.is_active,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="branches.update", entity=updated.id, metadata={"code": updated.code})
    return _to_response(updated)


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_branch(branch_id: str, auth: AuthContext = Depends(require_roles("admin"))) -> Response:
    try:
        branch_service.delete_branch(branch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="branches.delete", entity=branch_id, metadata={})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
