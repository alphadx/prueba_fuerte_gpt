from app.modules.payments.service import payment_service


def setup_function() -> None:
    payment_service.reset_state()


def test_feature_flag_blocks_stub_payment_when_disabled() -> None:
    payment_service.set_method_flag(branch_id="branch-1", channel="web", method="transbank_stub", enabled=False)

    try:
        payment_service.create_stub_payment(
            provider="transbank_stub",
            sale_id="sale-1",
            amount=15000,
            idempotency_key="idem-1",
            company_id="comp-1",
            branch_id="branch-1",
            channel="web",
        )
        assert False, "expected feature flag rejection"
    except ValueError as exc:
        assert str(exc) == "payment method disabled for branch/channel"


def test_feature_flag_allows_payment_when_enabled() -> None:
    payment_service.set_method_flag(branch_id="branch-1", channel="web", method="mercadopago_stub", enabled=True)

    created = payment_service.create_stub_payment(
        provider="mercadopago_stub",
        sale_id="sale-1",
        amount=15000,
        idempotency_key="idem-2",
        company_id="comp-1",
        branch_id="branch-1",
        channel="web",
    )
    assert created.status == "approved"
