"""Schemas for document types CRUD endpoints."""

from pydantic import BaseModel, Field


class DocumentTypeCreateRequest(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    requires_expiry: bool = True
    is_active: bool = True


class DocumentTypeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    requires_expiry: bool | None = None
    is_active: bool | None = None


class DocumentTypeResponse(BaseModel):
    id: str
    code: str
    name: str
    requires_expiry: bool
    is_active: bool


class DocumentTypeListResponse(BaseModel):
    items: list[DocumentTypeResponse]
