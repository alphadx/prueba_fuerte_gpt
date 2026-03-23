"""Payment gateway contract and canonical payment models for step 8."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class PaymentStatus(str, Enum):
    INITIATED = "initiated"
    PENDING_CONFIRMATION = "pending_confirmation"
    APPROVED = "approved"
    REJECTED = "rejected"
    RECONCILED = "reconciled"


_STATUS_ORDER: dict[PaymentStatus, int] = {
    PaymentStatus.INITIATED: 1,
    PaymentStatus.PENDING_CONFIRMATION: 2,
    PaymentStatus.APPROVED: 3,
    PaymentStatus.REJECTED: 3,
    PaymentStatus.RECONCILED: 4,
}


class PaymentErrorCode(str, Enum):
    INVALID_REQUEST = "invalid_request"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    UNKNOWN = "unknown"


class PaymentChannel(str, Enum):
    POS = "pos"
    WEB = "web"


@dataclass(frozen=True)
class PaymentIntent:
    idempotency_key: str
    sale_id: str
    company_id: str
    branch_id: str
    channel: PaymentChannel
    amount: float
    currency: str
    method: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentResult:
    provider: str
    provider_payment_id: str
    status: PaymentStatus
    error_code: PaymentErrorCode | None
    error_message: str | None
    raw_payload_ref: str


@dataclass(frozen=True)
class WebhookEvent:
    provider: str
    event_id: str
    idempotency_key: str
    provider_payment_id: str
    status: PaymentStatus
    signature: str | None
    payload: dict[str, str]


class PaymentGateway(Protocol):
    """Contract for payment adapter implementations."""

    provider_name: str

    def authorize(self, intent: PaymentIntent) -> PaymentResult:
        """Start payment authorization for a given intent."""

    def capture(self, intent: PaymentIntent) -> PaymentResult:
        """Capture a previously authorized payment if provider requires capture phase."""

    def parse_webhook(self, payload: dict[str, str], *, signature: str | None) -> WebhookEvent:
        """Normalize a provider webhook payload into the canonical webhook event model."""

    def validate_signature(self, payload: dict[str, str], *, signature: str | None) -> bool:
        """Validate webhook signature/metadata according to provider rules."""


def can_transition(current: PaymentStatus, target: PaymentStatus) -> bool:
    """Allow only forward, monotonic payment-state transitions."""

    if current == target:
        return True
    return _STATUS_ORDER[target] >= _STATUS_ORDER[current]
