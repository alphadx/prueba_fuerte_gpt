"""Document types API router with RBAC and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.document_types.schemas import (
    DocumentTypeCreateRequest,
    DocumentTypeListResponse,
    DocumentTypeResponse,
    DocumentTypeUpdateRequest,
)
from app.modules.document_types.service import DocumentType, document_type_service

router = APIRouter(prefix="/document-types", tags=["document-types"])


def _to_response(document_type: DocumentType) -> DocumentTypeResponse:
    return DocumentTypeResponse(
        id=document_type.id,
        code=document_type.code,
        name=document_type.name,
        requires_expiry=document_type.requires_expiry,
        is_active=document_type.is_active,
    )


@router.get("", response_model=DocumentTypeListResponse)
def list_document_types(_: AuthContext = Depends(require_roles("admin", "rrhh"))) -> DocumentTypeListResponse:
    return DocumentTypeListResponse(items=[_to_response(item) for item in document_type_service.list_document_types()])


@router.post("", response_model=DocumentTypeResponse, status_code=status.HTTP_201_CREATED)
def create_document_type(
    payload: DocumentTypeCreateRequest,
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> DocumentTypeResponse:
    try:
        created = document_type_service.create_document_type(
            code=payload.code,
            name=payload.name,
            requires_expiry=payload.requires_expiry,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="document_types.create",
        entity=created.id,
        metadata={"code": created.code},
    )
    return _to_response(created)


@router.get("/{document_type_id}", response_model=DocumentTypeResponse)
def get_document_type(
    document_type_id: str,
    _: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> DocumentTypeResponse:
    try:
        return _to_response(document_type_service.get_document_type(document_type_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{document_type_id}", response_model=DocumentTypeResponse)
def update_document_type(
    document_type_id: str,
    payload: DocumentTypeUpdateRequest,
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> DocumentTypeResponse:
    try:
        updated = document_type_service.update_document_type(
            document_type_id,
            name=payload.name,
            requires_expiry=payload.requires_expiry,
            is_active=payload.is_active,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="document_types.update",
        entity=updated.id,
        metadata={"code": updated.code},
    )
    return _to_response(updated)


@router.delete("/{document_type_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_document_type(
    document_type_id: str,
    auth: AuthContext = Depends(require_roles("admin")),
) -> Response:
    try:
        document_type_service.delete_document_type(document_type_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="document_types.delete",
        entity=document_type_id,
        metadata={},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
