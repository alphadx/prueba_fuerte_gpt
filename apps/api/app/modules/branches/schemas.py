"""Schemas for branches CRUD endpoints."""

from pydantic import BaseModel, Field


class BranchCreateRequest(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    address: str = Field(min_length=1)
    is_active: bool = True


class BranchUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    address: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class BranchResponse(BaseModel):
    id: str
    code: str
    name: str
    address: str
    is_active: bool


class BranchListResponse(BaseModel):
    items: list[BranchResponse]
