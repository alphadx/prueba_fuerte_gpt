"""Stub gateways for transbank and mercadopago payment flows."""

from __future__ import annotations

from app.modules.payments.gateway import (
    PaymentErrorCode,
    PaymentGateway,
    PaymentIntent,
    PaymentResult,
    PaymentStatus,
    WebhookEvent,
)


class _BaseStubGateway(PaymentGateway):
    provider_name = "stub"

    def authorize(self, intent: PaymentIntent) -> PaymentResult:
        status = PaymentStatus.PENDING_CONFIRMATION
        error_code = None
        error_message = None

        if intent.metadata.get("force_reject") == "true":
            status = PaymentStatus.REJECTED
            error_code = PaymentErrorCode.REJECTED
            error_message = "forced rejection"
        elif intent.metadata.get("force_timeout") == "true":
            status = PaymentStatus.REJECTED
            error_code = PaymentErrorCode.TIMEOUT
            error_message = "forced timeout"

        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"{self.provider_name}-{intent.idempotency_key}",
            status=status,
            error_code=error_code,
            error_message=error_message,
            raw_payload_ref=f"{self.provider_name}://authorize/{intent.idempotency_key}",
        )

    def capture(self, intent: PaymentIntent) -> PaymentResult:
        if intent.metadata.get("force_reject") == "true":
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id=f"{self.provider_name}-{intent.idempotency_key}",
                status=PaymentStatus.REJECTED,
                error_code=PaymentErrorCode.REJECTED,
                error_message="forced rejection",
                raw_payload_ref=f"{self.provider_name}://capture/{intent.idempotency_key}",
            )

        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"{self.provider_name}-{intent.idempotency_key}",
            status=PaymentStatus.APPROVED,
            error_code=None,
            error_message=None,
            raw_payload_ref=f"{self.provider_name}://capture/{intent.idempotency_key}",
        )

    def parse_webhook(self, payload: dict[str, str], *, signature: str | None) -> WebhookEvent:
        status = PaymentStatus(payload.get("status", PaymentStatus.PENDING_CONFIRMATION.value))
        return WebhookEvent(
            provider=self.provider_name,
            event_id=payload.get("event_id", f"{self.provider_name}-event"),
            idempotency_key=payload.get("idempotency_key", "unknown"),
            provider_payment_id=payload.get("provider_payment_id", "unknown"),
            status=status,
            signature=signature,
            payload=payload,
        )

    def validate_signature(self, payload: dict[str, str], *, signature: str | None) -> bool:
        return signature is not None and signature.startswith(f"{self.provider_name}:")


class TransbankStubGateway(_BaseStubGateway):
    provider_name = "transbank_stub"


class MercadopagoStubGateway(_BaseStubGateway):
    provider_name = "mercadopago_stub"


transbank_stub_gateway = TransbankStubGateway()
mercadopago_stub_gateway = MercadopagoStubGateway()


gateway_registry: dict[str, PaymentGateway] = {
    transbank_stub_gateway.provider_name: transbank_stub_gateway,
    mercadopago_stub_gateway.provider_name: mercadopago_stub_gateway,
}
