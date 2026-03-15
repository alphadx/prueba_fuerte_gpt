"""Schemas for payments CRUD endpoints."""

from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    sale_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    method: str = Field(min_length=1)
    status: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)


class PaymentUpdateRequest(BaseModel):
    status: str | None = Field(default=None, min_length=1)


class PaymentResponse(BaseModel):
    id: str
    sale_id: str
    amount: float
    method: str
    status: str
    idempotency_key: str


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
