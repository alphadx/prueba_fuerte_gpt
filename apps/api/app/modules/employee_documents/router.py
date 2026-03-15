"""Employee documents API router with RBAC and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.employee_documents.schemas import (
    EmployeeDocumentCreateRequest,
    EmployeeDocumentListResponse,
    EmployeeDocumentResponse,
    EmployeeDocumentUpdateRequest,
)
from app.modules.employee_documents.service import EmployeeDocument, employee_document_service

router = APIRouter(prefix="/employee-documents", tags=["employee-documents"])


def _to_response(item: EmployeeDocument) -> EmployeeDocumentResponse:
    return EmployeeDocumentResponse(
        id=item.id,
        employee_id=item.employee_id,
        document_type_code=item.document_type_code,
        expires_on=item.expires_on,
        status=item.status,
    )


@router.get("", response_model=EmployeeDocumentListResponse)
def list_documents(_: AuthContext = Depends(require_roles("admin", "rrhh"))) -> EmployeeDocumentListResponse:
    return EmployeeDocumentListResponse(items=[_to_response(doc) for doc in employee_document_service.list_documents()])


@router.post("", response_model=EmployeeDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: EmployeeDocumentCreateRequest,
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> EmployeeDocumentResponse:
    try:
        created = employee_document_service.create_document(
            employee_id=payload.employee_id,
            document_type_code=payload.document_type_code,
            expires_on=payload.expires_on,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="employee_documents.create",
        entity=created.id,
        metadata={"employee_id": created.employee_id, "document_type_code": created.document_type_code},
    )
    return _to_response(created)


@router.get("/{document_id}", response_model=EmployeeDocumentResponse)
def get_document(document_id: str, _: AuthContext = Depends(require_roles("admin", "rrhh"))) -> EmployeeDocumentResponse:
    try:
        return _to_response(employee_document_service.get_document(document_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{document_id}", response_model=EmployeeDocumentResponse)
def update_document(
    document_id: str,
    payload: EmployeeDocumentUpdateRequest,
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> EmployeeDocumentResponse:
    try:
        updated = employee_document_service.update_document(
            document_id,
            expires_on=payload.expires_on,
            status=payload.status,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="employee_documents.update",
        entity=updated.id,
        metadata={"status": updated.status},
    )
    return _to_response(updated)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_document(document_id: str, auth: AuthContext = Depends(require_roles("admin"))) -> Response:
    try:
        employee_document_service.delete_document(document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="employee_documents.delete",
        entity=document_id,
        metadata={},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
