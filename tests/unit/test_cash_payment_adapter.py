from app.modules.payments.cash_adapter import cash_payment_gateway
from app.modules.payments.gateway import PaymentChannel, PaymentIntent, PaymentStatus
from app.modules.payments.service import payment_service


def setup_function() -> None:
    payment_service.reset_state()


def test_cash_adapter_authorize_returns_approved() -> None:
    intent = PaymentIntent(
        idempotency_key="idem-cash-1",
        sale_id="sale-1",
        company_id="comp-1",
        branch_id="branch-1",
        channel=PaymentChannel.POS,
        amount=19990,
        currency="CLP",
        method="cash",
    )

    result = cash_payment_gateway.authorize(intent)
    assert result.status == PaymentStatus.APPROVED
    assert result.provider == "cash"


def test_payment_service_create_cash_and_reconcile_branch() -> None:
    approved = payment_service.create_cash_payment(
        sale_id="sale-1",
        amount=12000,
        idempotency_key="idem-cash-a",
        company_id="comp-1",
        branch_id="branch-1",
        channel="pos",
    )
    assert approved.status == "approved"

    payment_service.create_payment(
        sale_id="sale-2",
        amount=8000,
        method="cash",
        status="pending_confirmation",
        idempotency_key="idem-cash-b",
        branch_id="branch-1",
        channel="pos",
    )

    report = payment_service.reconcile_cash_by_branch(branch_id="branch-1")
    assert report["payments_total"] == 2
    assert report["approved_total"] == 1
    assert report["pending_total"] == 1
    assert report["amount_total"] == 20000
    assert report["amount_approved"] == 12000
