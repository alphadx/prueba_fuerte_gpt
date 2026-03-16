"""Schemas for employee documents CRUD endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class EmployeeDocumentCreateRequest(BaseModel):
    employee_id: str = Field(min_length=1)
    document_type_code: str = Field(min_length=1)
    issue_on: str = Field(min_length=1)
    expires_on: str = Field(min_length=1)
    status: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmployeeDocumentUpdateRequest(BaseModel):
    issue_on: str | None = Field(default=None, min_length=1)
    expires_on: str | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, min_length=1)
    metadata: dict[str, Any] | None = None


class EmployeeDocumentFileUploadRequest(BaseModel):
    file_name: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    storage_uri: str = Field(min_length=1)
    uploaded_at: str = Field(min_length=1)


class EmployeeDocumentFileResponse(BaseModel):
    id: str
    employee_document_id: str
    file_name: str
    content_type: str
    storage_uri: str
    uploaded_at: str


class EmployeeDocumentResponse(BaseModel):
    id: str
    employee_id: str
    document_type_code: str
    issue_on: str
    expires_on: str
    status: str
    metadata: dict[str, Any]


class EmployeeDocumentListResponse(BaseModel):
    items: list[EmployeeDocumentResponse]


class EmployeeDocumentFileListResponse(BaseModel):
    items: list[EmployeeDocumentFileResponse]
