"""Schemas for e-commerce pickup checkout (step 9 - stage 7)."""

from pydantic import BaseModel, Field


class CatalogProductResponse(BaseModel):
    product_id: str
    sku: str
    name: str
    price: float
    currency: str = "CLP"
    available_stock: float
    branch_id: str
    is_pickup_enabled: bool = True


class CatalogProductListResponse(BaseModel):
    items: list[CatalogProductResponse]


class PickupSlotResponse(BaseModel):
    pickup_slot_id: str
    start_at: str
    end_at: str
    status: str
    remaining_capacity: int = Field(ge=0)


class PickupSlotListResponse(BaseModel):
    branch_id: str
    date: str
    slots: list[PickupSlotResponse]


class CheckoutCustomerRequest(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=3)
    phone: str = Field(min_length=8)


class CheckoutLineRequest(BaseModel):
    product_id: str = Field(min_length=1)
    qty: float = Field(gt=0)


class PickupCheckoutConfirmRequest(BaseModel):
    branch_id: str = Field(min_length=1)
    pickup_slot_id: str = Field(min_length=1)
    customer: CheckoutCustomerRequest
    lines: list[CheckoutLineRequest] = Field(min_length=1)


class OrderLineResponse(BaseModel):
    product_id: str
    qty: float
    unit_price: float
    line_total: float


class OrderTransitionEventResponse(BaseModel):
    previous_state: str
    current_state: str
    actor: str
    reason: str


class PickupCheckoutConfirmResponse(BaseModel):
    order_id: str
    order_state: str
    branch_id: str
    pickup_slot_id: str
    totals: dict[str, float | str]
    idempotency_key: str
    lines: list[OrderLineResponse]


class PickupOrderResponse(BaseModel):
    order_id: str
    state: str
    branch_id: str
    pickup_slot_id: str
    customer: dict[str, str]
    idempotency_key: str
    lines: list[OrderLineResponse]
    subtotal: float
    transitions: list[OrderTransitionEventResponse]


class OrderTransitionRequest(BaseModel):
    target_state: str = Field(min_length=1)
    reason: str = Field(min_length=3)


class OrderTransitionResponse(BaseModel):
    order_id: str
    previous_state: str
    current_state: str


class OrderObservabilityResponse(BaseModel):
    total_orders: int
    states: dict[str, int]
    delivered_orders: int
    rejected_checkouts: int
    rejected_transitions: int
    idempotent_replays: int


class OrderConsistencyReportResponse(BaseModel):
    total_orders: int
    orders_with_inconsistencies: int
    inconsistencies: list[str]
