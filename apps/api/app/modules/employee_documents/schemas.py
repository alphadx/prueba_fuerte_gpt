"""Schemas for employee documents CRUD endpoints."""

from pydantic import BaseModel, Field


class EmployeeDocumentCreateRequest(BaseModel):
    employee_id: str = Field(min_length=1)
    document_type_code: str = Field(min_length=1)
    expires_on: str = Field(min_length=1)
    status: str = Field(min_length=1)


class EmployeeDocumentUpdateRequest(BaseModel):
    expires_on: str | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, min_length=1)


class EmployeeDocumentResponse(BaseModel):
    id: str
    employee_id: str
    document_type_code: str
    expires_on: str
    status: str


class EmployeeDocumentListResponse(BaseModel):
    items: list[EmployeeDocumentResponse]
