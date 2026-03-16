"""Cash payment adapter for local POS settlement and reconciliation."""

from __future__ import annotations

from app.modules.payments.gateway import (
    PaymentErrorCode,
    PaymentGateway,
    PaymentIntent,
    PaymentResult,
    PaymentStatus,
    WebhookEvent,
)


class CashPaymentGateway(PaymentGateway):
    provider_name = "cash"

    def authorize(self, intent: PaymentIntent) -> PaymentResult:
        if intent.amount <= 0:
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id=f"cash-{intent.idempotency_key}",
                status=PaymentStatus.REJECTED,
                error_code=PaymentErrorCode.INVALID_REQUEST,
                error_message="amount must be positive",
                raw_payload_ref=f"cash://authorize/{intent.idempotency_key}",
            )

        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"cash-{intent.idempotency_key}",
            status=PaymentStatus.APPROVED,
            error_code=None,
            error_message=None,
            raw_payload_ref=f"cash://authorize/{intent.idempotency_key}",
        )

    def capture(self, intent: PaymentIntent) -> PaymentResult:
        # Cash is settled immediately; capture is equivalent to authorize.
        return self.authorize(intent)

    def parse_webhook(self, payload: dict[str, str], *, signature: str | None) -> WebhookEvent:
        # Cash has no external callback. This normalizes manual settlement events if ever provided.
        event_id = payload.get("event_id", "cash-manual")
        payment_id = payload.get("provider_payment_id", "cash-manual")
        idem = payload.get("idempotency_key", "cash-manual")
        status = PaymentStatus(payload.get("status", PaymentStatus.APPROVED.value))

        return WebhookEvent(
            provider=self.provider_name,
            event_id=event_id,
            idempotency_key=idem,
            provider_payment_id=payment_id,
            status=status,
            signature=signature,
            payload=payload,
        )

    def validate_signature(self, payload: dict[str, str], *, signature: str | None) -> bool:
        # No signature requirement for local cash events.
        return True


cash_payment_gateway = CashPaymentGateway()
