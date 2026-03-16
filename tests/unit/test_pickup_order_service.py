from app.modules.orders.service import pickup_order_service
from app.modules.products.service import product_service


def setup_function() -> None:
    product_service.reset_state()
    pickup_order_service.reset_state()


def _create_product(*, sku: str, stock: float) -> str:
    product = product_service.create_product(sku=sku, name=sku, price=1000)
    product_service.set_stock(product.id, stock)
    return product.id


def test_create_order_decrements_stock_and_sets_received_state() -> None:
    product_id = _create_product(sku="SKU-1", stock=5)

    order = pickup_order_service.create_order(
        branch_id="br-001",
        pickup_slot_id="slot-10-11",
        customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        lines_payload=[{"product_id": product_id, "qty": 2}],
        idempotency_key="idem-1",
    )

    assert order.state == "recibido"
    assert order.order_id.startswith("ord-")
    assert product_service.get_stock(product_id) == 3
    assert order.transitions == []


def test_create_order_is_idempotent_by_key() -> None:
    product_id = _create_product(sku="SKU-2", stock=5)

    first = pickup_order_service.create_order(
        branch_id="br-001",
        pickup_slot_id="slot-10-11",
        customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        lines_payload=[{"product_id": product_id, "qty": 2}],
        idempotency_key="idem-2",
    )
    second = pickup_order_service.create_order(
        branch_id="br-001",
        pickup_slot_id="slot-10-11",
        customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        lines_payload=[{"product_id": product_id, "qty": 2}],
        idempotency_key="idem-2",
    )

    assert first.order_id == second.order_id
    assert product_service.get_stock(product_id) == 3


def test_create_order_rolls_back_when_stock_insufficient() -> None:
    product_id = _create_product(sku="SKU-3", stock=1)

    try:
        pickup_order_service.create_order(
            branch_id="br-001",
            pickup_slot_id="slot-10-11",
            customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
            lines_payload=[{"product_id": product_id, "qty": 2}],
            idempotency_key="idem-3",
        )
    except ValueError as exc:
        assert "stock" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    assert product_service.get_stock(product_id) == 1


def test_transition_order_accepts_only_forward_states() -> None:
    product_id = _create_product(sku="SKU-4", stock=5)
    order = pickup_order_service.create_order(
        branch_id="br-001",
        pickup_slot_id="slot-10-11",
        customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        lines_payload=[{"product_id": product_id, "qty": 1}],
        idempotency_key="idem-4",
    )

    updated = pickup_order_service.transition_order(
        order_id=order.order_id,
        target_state="preparado",
        actor="usr-1",
        reason="pedido preparado",
    )
    assert updated.state == "preparado"

    try:
        pickup_order_service.transition_order(
            order_id=order.order_id,
            target_state="entregado",
            actor="usr-1",
            reason="salto invalido",
        )
    except ValueError as exc:
        assert "invalid" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_transition_order_records_history() -> None:
    product_id = _create_product(sku="SKU-5", stock=5)
    order = pickup_order_service.create_order(
        branch_id="br-001",
        pickup_slot_id="slot-10-11",
        customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        lines_payload=[{"product_id": product_id, "qty": 1}],
        idempotency_key="idem-5",
    )

    pickup_order_service.transition_order(
        order_id=order.order_id,
        target_state="preparado",
        actor="usr-1",
        reason="bodega",
    )
    pickup_order_service.transition_order(
        order_id=order.order_id,
        target_state="listo_para_retiro",
        actor="usr-1",
        reason="mostrador",
    )

    fetched = pickup_order_service.get_order(order.order_id)
    assert [item.current_state for item in fetched.transitions] == ["preparado", "listo_para_retiro"]


def test_observability_snapshot_counts_rejections_and_replays() -> None:
    product_id = _create_product(sku="SKU-6", stock=5)

    pickup_order_service.create_order(
        branch_id="br-001",
        pickup_slot_id="slot-10-11",
        customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        lines_payload=[{"product_id": product_id, "qty": 1}],
        idempotency_key="idem-6",
    )
    pickup_order_service.create_order(
        branch_id="br-001",
        pickup_slot_id="slot-10-11",
        customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        lines_payload=[{"product_id": product_id, "qty": 1}],
        idempotency_key="idem-6",
    )
    pickup_order_service.register_checkout_rejection()
    pickup_order_service.register_transition_rejection()

    snapshot = pickup_order_service.get_observability_snapshot()
    assert snapshot.total_orders == 1
    assert snapshot.states["recibido"] == 1
    assert snapshot.idempotent_replays == 1
    assert snapshot.rejected_checkouts == 1
    assert snapshot.rejected_transitions == 1


def test_consistency_report_detects_clean_state() -> None:
    product_id = _create_product(sku="SKU-7", stock=5)

    pickup_order_service.create_order(
        branch_id="br-001",
        pickup_slot_id="slot-10-11",
        customer={"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        lines_payload=[{"product_id": product_id, "qty": 1}],
        idempotency_key="idem-7",
    )

    report = pickup_order_service.run_consistency_report()
    assert report.total_orders == 1
    assert report.orders_with_inconsistencies == 0
    assert report.inconsistencies == []
