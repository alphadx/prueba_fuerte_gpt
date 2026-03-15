from app.modules.payments.service import payment_service


def setup_function() -> None:
    payment_service.reset_state()


def test_payment_service_create_get_update_delete() -> None:
    created = payment_service.create_payment(
        sale_id="sale-001",
        amount=15990,
        method="efectivo",
        status="pending",
        idempotency_key="idem-001",
    )

    fetched = payment_service.get_payment(created.id)
    assert fetched.sale_id == "sale-001"

    updated = payment_service.update_payment(created.id, status="paid")
    assert updated.status == "paid"

    payment_service.delete_payment(created.id)

    try:
        payment_service.get_payment(created.id)
        assert False, "expected KeyError"
    except KeyError as exc:
        assert str(exc) == "'payment not found'"


def test_payment_service_reject_duplicate_idempotency_key() -> None:
    payment_service.create_payment(
        sale_id="sale-001",
        amount=15990,
        method="efectivo",
        status="pending",
        idempotency_key="idem-001",
    )

    try:
        payment_service.create_payment(
            sale_id="sale-001",
            amount=15990,
            method="efectivo",
            status="pending",
            idempotency_key="idem-001",
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "idempotency key already exists"
