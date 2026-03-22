from app.modules.cash_sessions.service import cash_session_service
from app.modules.products.service import product_service
from app.modules.sales.service import sale_service


def setup_function() -> None:
    product_service.reset_state()
    cash_session_service.reset_state()
    sale_service.reset_state()


def test_sale_service_maps_payment_states_deterministically(monkeypatch) -> None:
    monkeypatch.setattr("app.modules.sales.service.billing_service.enqueue_sale_emission_event", lambda **kwargs: None)

    product = product_service.create_product(sku="SKU-1", name="Pan", price=1000)
    product_service.set_stock(product.id, 10)
    session = cash_session_service.create_session(
        branch_id="br-001", opened_by="usr-001", opening_amount=0, status="open"
    )

    sale_cash = sale_service.complete_sale(
        branch_id="br-001",
        cash_session_id=session.id,
        sold_by="usr-001",
        payment_method="cash",
        lines_payload=[{"product_id": product.id, "quantity": 1}],
    )
    assert sale_cash.payment_status == "approved"
    assert sale_cash.status == "paid"

    sale_card = sale_service.complete_sale(
        branch_id="br-001",
        cash_session_id=session.id,
        sold_by="usr-001",
        payment_method="card_stub",
        lines_payload=[{"product_id": product.id, "quantity": 1}],
    )
    assert sale_card.payment_status == "pending"
    assert sale_card.status == "confirmed"


def test_sale_service_rejects_branch_mismatch(monkeypatch) -> None:
    monkeypatch.setattr("app.modules.sales.service.billing_service.enqueue_sale_emission_event", lambda **kwargs: None)

    product = product_service.create_product(sku="SKU-2", name="Leche", price=1200)
    product_service.set_stock(product.id, 10)
    session = cash_session_service.create_session(
        branch_id="br-001", opened_by="usr-001", opening_amount=0, status="open"
    )

    try:
        sale_service.complete_sale(
            branch_id="br-999",
            cash_session_id=session.id,
            sold_by="usr-001",
            payment_method="cash",
            lines_payload=[{"product_id": product.id, "quantity": 1}],
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "cash session branch mismatch"


def test_sale_service_rolls_back_partial_stock_and_kardex(monkeypatch) -> None:
    monkeypatch.setattr("app.modules.sales.service.billing_service.enqueue_sale_emission_event", lambda **kwargs: None)

    p1 = product_service.create_product(sku="SKU-3", name="Arroz", price=1800)
    p2 = product_service.create_product(sku="SKU-4", name="Aceite", price=4200)
    product_service.set_stock(p1.id, 5)
    product_service.set_stock(p2.id, 1)
    session = cash_session_service.create_session(
        branch_id="br-001", opened_by="usr-001", opening_amount=0, status="open"
    )

    try:
        sale_service.complete_sale(
            branch_id="br-001",
            cash_session_id=session.id,
            sold_by="usr-001",
            payment_method="cash",
            lines_payload=[
                {"product_id": p1.id, "quantity": 2},
                {"product_id": p2.id, "quantity": 2},
            ],
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "stock update failed; sale rolled back"

    assert product_service.get_stock(p1.id) == 5
    assert product_service.get_stock(p2.id) == 1
    assert product_service.list_stock_movements() == []
    assert sale_service.list_sales() == []
