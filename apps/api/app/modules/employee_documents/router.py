"""Employee documents API router with RBAC and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.document_types.service import DocumentSchemaValidationError, document_type_service
from app.modules.employee_documents.file_storage import (
    EmployeeDocumentFile,
    employee_document_file_storage_service,
)
from app.modules.employee_documents.schemas import (
    EmployeeDocumentCreateRequest,
    EmployeeDocumentFileListResponse,
    EmployeeDocumentFileResponse,
    EmployeeDocumentFileUploadRequest,
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
        issue_on=item.issue_on,
        expires_on=item.expires_on,
        status=item.status,
        metadata=item.metadata,
    )


def _to_file_response(item: EmployeeDocumentFile) -> EmployeeDocumentFileResponse:
    return EmployeeDocumentFileResponse(
        id=item.id,
        employee_document_id=item.employee_document_id,
        file_name=item.file_name,
        content_type=item.content_type,
        storage_uri=item.storage_uri,
        uploaded_at=item.uploaded_at,
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
        document_type_service.validate_metadata(document_type_code=payload.document_type_code, metadata=payload.metadata)
        created = employee_document_service.create_document(
            employee_id=payload.employee_id,
            document_type_code=payload.document_type_code,
            issue_on=payload.issue_on,
            expires_on=payload.expires_on,
            status=payload.status,
            metadata=payload.metadata,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DocumentSchemaValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="employee_documents.create",
        entity=created.id,
        metadata={
            "employee_id": created.employee_id,
            "document_type_code": created.document_type_code,
            "issue_on": created.issue_on,
            "expires_on": created.expires_on,
        },
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
        current = employee_document_service.get_document(document_id)
        new_metadata = payload.metadata if payload.metadata is not None else current.metadata
        document_type_service.validate_metadata(document_type_code=current.document_type_code, metadata=new_metadata)
        updated = employee_document_service.update_document(
            document_id,
            issue_on=payload.issue_on,
            expires_on=payload.expires_on,
            status=payload.status,
            metadata=payload.metadata,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentSchemaValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="employee_documents.update",
        entity=updated.id,
        metadata={"status": updated.status, "expires_on": updated.expires_on},
    )
    return _to_response(updated)


@router.post("/{document_id}/files", response_model=EmployeeDocumentFileResponse, status_code=status.HTTP_201_CREATED)
def upload_document_file(
    document_id: str,
    payload: EmployeeDocumentFileUploadRequest,
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> EmployeeDocumentFileResponse:
    try:
        employee_document_service.get_document(document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    created_file = employee_document_file_storage_service.create_file(
        employee_document_id=document_id,
        file_name=payload.file_name,
        content_type=payload.content_type,
        storage_uri=payload.storage_uri,
        uploaded_at=payload.uploaded_at,
    )

    record_audit_event(
        actor_id=auth.subject,
        action="employee_documents.file_upload",
        entity=document_id,
        metadata={"file_id": created_file.id, "storage_uri": created_file.storage_uri},
    )
    return _to_file_response(created_file)


@router.get("/{document_id}/files", response_model=EmployeeDocumentFileListResponse)
def list_document_files(
    document_id: str,
    _: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> EmployeeDocumentFileListResponse:
    try:
        employee_document_service.get_document(document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    files = employee_document_file_storage_service.list_files(employee_document_id=document_id)
    return EmployeeDocumentFileListResponse(items=[_to_file_response(item) for item in files])


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
