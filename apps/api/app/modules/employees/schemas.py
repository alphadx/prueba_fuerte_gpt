"""Schemas for employees CRUD endpoints."""

from pydantic import BaseModel, Field


class EmployeeCreateRequest(BaseModel):
    employee_code: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    is_active: bool = True


class EmployeeUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    role: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: str
    employee_code: str
    full_name: str
    role: str
    is_active: bool


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
