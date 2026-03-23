"""Schemas for document types CRUD endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class DocumentTypeCreateRequest(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    requires_expiry: bool = True
    is_active: bool = True
    schema_version: int = Field(default=1, ge=1)
    metadata_schema: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}, "required": []}
    )


class DocumentTypeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    requires_expiry: bool | None = None
    is_active: bool | None = None
    schema_version: int | None = Field(default=None, ge=1)
    metadata_schema: dict[str, Any] | None = None


class DocumentTypeResponse(BaseModel):
    id: str
    code: str
    name: str
    requires_expiry: bool
    is_active: bool
    schema_version: int
    metadata_schema: dict[str, Any]


class DocumentTypeListResponse(BaseModel):
    items: list[DocumentTypeResponse]
