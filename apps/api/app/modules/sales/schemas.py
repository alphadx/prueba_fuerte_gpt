"""Schemas for POS sale completion endpoints."""

from pydantic import BaseModel, Field


class SaleLineRequest(BaseModel):
    product_id: str = Field(min_length=1)
    quantity: float = Field(gt=0)


class SaleCompleteRequest(BaseModel):
    branch_id: str = Field(min_length=1)
    cash_session_id: str = Field(min_length=1)
    sold_by: str = Field(min_length=1)
    payment_method: str = Field(min_length=1)
    lines: list[SaleLineRequest] = Field(min_length=1)


class SaleLineResponse(BaseModel):
    product_id: str
    quantity: float
    unit_price: float
    line_subtotal: float
    line_tax: float
    line_total: float


class SaleResponse(BaseModel):
    id: str
    branch_id: str
    cash_session_id: str
    sold_by: str
    status: str
    subtotal: float
    taxes: float
    total: float
    payment_method: str
    payment_status: str
    billing_event_emitted: bool
    lines: list[SaleLineResponse]


class SaleListResponse(BaseModel):
    items: list[SaleResponse]
