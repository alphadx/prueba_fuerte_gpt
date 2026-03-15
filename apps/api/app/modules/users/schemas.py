"""Schemas for users CRUD endpoints."""

from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3)
    full_name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    role: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    is_active: bool


class UserListResponse(BaseModel):
    items: list[UserResponse]
