from app.modules.payments.gateway import (
    PaymentChannel,
    PaymentErrorCode,
    PaymentIntent,
    PaymentResult,
    PaymentStatus,
    WebhookEvent,
    can_transition,
)


def test_payment_canonical_models_smoke() -> None:
    intent = PaymentIntent(
        idempotency_key="idem-1",
        sale_id="sale-1",
        company_id="comp-1",
        branch_id="branch-1",
        channel=PaymentChannel.POS,
        amount=1000,
        currency="CLP",
        method="cash",
        metadata={"terminal_id": "t-1"},
    )

    result = PaymentResult(
        provider="cash",
        provider_payment_id="cash-1",
        status=PaymentStatus.APPROVED,
        error_code=None,
        error_message=None,
        raw_payload_ref="cash://tx/1",
    )

    event = WebhookEvent(
        provider="transbank_stub",
        event_id="evt-1",
        idempotency_key=intent.idempotency_key,
        provider_payment_id="tbk-1",
        status=PaymentStatus.PENDING_CONFIRMATION,
        signature="sig",
        payload={"amount": "1000"},
    )

    assert intent.channel == PaymentChannel.POS
    assert result.status == PaymentStatus.APPROVED
    assert event.provider == "transbank_stub"


def test_payment_status_transition_is_monotonic() -> None:
    assert can_transition(PaymentStatus.INITIATED, PaymentStatus.PENDING_CONFIRMATION)
    assert can_transition(PaymentStatus.PENDING_CONFIRMATION, PaymentStatus.APPROVED)
    assert can_transition(PaymentStatus.APPROVED, PaymentStatus.RECONCILED)
    assert not can_transition(PaymentStatus.RECONCILED, PaymentStatus.APPROVED)


def test_payment_error_codes_include_expected_timeout_family() -> None:
    assert PaymentErrorCode.TIMEOUT.value == "timeout"
    assert PaymentErrorCode.PROVIDER_UNAVAILABLE.value == "provider_unavailable"
