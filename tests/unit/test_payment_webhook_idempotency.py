from app.modules.payments.service import payment_service


def setup_function() -> None:
    payment_service.reset_state()


def test_webhook_idempotency_and_signature_validation() -> None:
    created = payment_service.create_stub_payment(
        provider="transbank_stub",
        sale_id="sale-1",
        amount=20000,
        idempotency_key="idem-1",
        company_id="comp-1",
        branch_id="branch-1",
        channel="web",
    )

    first = payment_service.process_webhook_event(
        provider="transbank_stub",
        payload={
            "event_id": "evt-1",
            "idempotency_key": "idem-1",
            "provider_payment_id": f"transbank_stub-idem-1",
            "status": "reconciled",
        },
        signature="transbank_stub:ok",
    )
    assert not first.duplicated
    assert first.payment_id == created.id
    assert first.current_status == "reconciled"

    duplicated = payment_service.process_webhook_event(
        provider="transbank_stub",
        payload={
            "event_id": "evt-1",
            "idempotency_key": "idem-1",
            "provider_payment_id": f"transbank_stub-idem-1",
            "status": "reconciled",
        },
        signature="transbank_stub:ok",
    )
    assert duplicated.duplicated

    try:
        payment_service.process_webhook_event(
            provider="transbank_stub",
            payload={"event_id": "evt-2", "provider_payment_id": "transbank_stub-idem-1", "status": "approved"},
            signature="bad-signature",
        )
        assert False, "expected invalid signature"
    except ValueError as exc:
        assert str(exc) == "invalid signature"
