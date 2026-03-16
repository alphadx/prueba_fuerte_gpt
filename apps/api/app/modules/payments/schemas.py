"""Schemas for payments CRUD endpoints."""

from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    sale_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    method: str = Field(min_length=1)
    status: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)


class CashPaymentCreateRequest(BaseModel):
    sale_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(default="CLP", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=1)




class StubPaymentCreateRequest(BaseModel):
    sale_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(default="CLP", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)

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


class CashReconciliationResponse(BaseModel):
    branch_id: str
    payments_total: int
    approved_total: int
    pending_total: int
    amount_total: float
    amount_approved: float
