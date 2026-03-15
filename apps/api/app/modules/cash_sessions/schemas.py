"""Schemas for cash sessions CRUD endpoints."""

from pydantic import BaseModel, Field


class CashSessionCreateRequest(BaseModel):
    branch_id: str = Field(min_length=1)
    opened_by: str = Field(min_length=1)
    opening_amount: float = Field(ge=0)
    status: str = Field(min_length=1)


class CashSessionUpdateRequest(BaseModel):
    closing_amount: float | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, min_length=1)


class CashSessionResponse(BaseModel):
    id: str
    branch_id: str
    opened_by: str
    opening_amount: float
    closing_amount: float | None
    status: str


class CashSessionListResponse(BaseModel):
    items: list[CashSessionResponse]
