from app.modules.payments.gateway import PaymentChannel, PaymentIntent, PaymentStatus
from app.modules.payments.stub_adapters import mercadopago_stub_gateway, transbank_stub_gateway


def _intent(idem: str, metadata: dict[str, str] | None = None) -> PaymentIntent:
    return PaymentIntent(
        idempotency_key=idem,
        sale_id="sale-1",
        company_id="comp-1",
        branch_id="branch-1",
        channel=PaymentChannel.WEB,
        amount=15000,
        currency="CLP",
        method="stub",
        metadata=metadata or {},
    )


def test_stub_gateways_authorize_capture_happy_path() -> None:
    for gateway in (transbank_stub_gateway, mercadopago_stub_gateway):
        authorized = gateway.authorize(_intent(f"idem-{gateway.provider_name}"))
        assert authorized.status == PaymentStatus.PENDING_CONFIRMATION

        captured = gateway.capture(_intent(f"idem-{gateway.provider_name}"))
        assert captured.status == PaymentStatus.APPROVED


def test_stub_gateway_force_reject_path() -> None:
    authorized = transbank_stub_gateway.authorize(_intent("idem-reject", {"force_reject": "true"}))
    assert authorized.status == PaymentStatus.REJECTED

    captured = transbank_stub_gateway.capture(_intent("idem-reject", {"force_reject": "true"}))
    assert captured.status == PaymentStatus.REJECTED
