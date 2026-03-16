import base64
import hashlib
import hmac
import json

import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import app
from app.modules.orders.service import pickup_order_service
from app.modules.products.service import product_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    product_service.reset_state()
    pickup_order_service.reset_state()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _token(*, sub: str, roles: list[str], secret: str = "test-secret") -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({"sub": sub, "roles": roles}).encode())
    signing_input = f"{header}.{payload}"
    signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def _auth_header(*, roles: list[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(sub='user-1', roles=roles)}"}


def _create_product(*, sku: str, stock: float) -> str:
    headers = _auth_header(roles=["admin"])
    response = client.post(
        "/products",
        json={"sku": sku, "name": sku, "price": 1000},
        headers=headers,
    )
    assert response.status_code == 201
    product_id = response.json()["id"]
    product_service.set_stock(product_id, stock)
    return product_id


def _create_pickup_order(*, idempotency_key: str = "idem-checkout") -> str:
    headers = _auth_header(roles=["cajero"])
    product_id = _create_product(sku=f"SKU-{idempotency_key}", stock=4)
    response = client.post(
        "/checkout/pickup/confirm",
        headers={**headers, "Idempotency-Key": idempotency_key},
        json={
            "branch_id": "br-001",
            "pickup_slot_id": "slot-10-11",
            "customer": {"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
            "lines": [{"product_id": product_id, "qty": 1}],
        },
    )
    assert response.status_code == 201
    return response.json()["order_id"]


def test_pickup_checkout_requires_authentication() -> None:
    response = client.post(
        "/checkout/pickup/confirm",
        headers={"Idempotency-Key": "idem-1"},
        json={
            "branch_id": "br-001",
            "pickup_slot_id": "slot-10-11",
            "customer": {"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
            "lines": [{"product_id": "prod-001", "qty": 1}],
        },
    )

    assert response.status_code == 401


def test_catalog_and_pickup_slots_exposed_for_branch() -> None:
    product_id = _create_product(sku="SKU-CAT-1", stock=7)
    headers = _auth_header(roles=["cajero"])

    catalog_response = client.get("/catalog/products", params={"branch_id": "br-001"}, headers=headers)
    assert catalog_response.status_code == 200
    assert any(item["product_id"] == product_id for item in catalog_response.json()["items"])

    slots_response = client.get(
        "/pickup-slots",
        params={"branch_id": "br-001", "date": "2026-03-16"},
        headers=headers,
    )
    assert slots_response.status_code == 200
    assert slots_response.json()["slots"]


def test_pickup_checkout_confirm_decrements_stock_and_is_idempotent() -> None:
    headers = _auth_header(roles=["cajero"])
    product_id = _create_product(sku="SKU-CHK-1", stock=4)

    payload = {
        "branch_id": "br-001",
        "pickup_slot_id": "slot-10-11",
        "customer": {"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
        "lines": [{"product_id": product_id, "qty": 2}],
    }

    first = client.post(
        "/checkout/pickup/confirm",
        headers={**headers, "Idempotency-Key": "idem-checkout-1"},
        json=payload,
    )
    assert first.status_code == 201
    first_body = first.json()
    assert first_body["order_state"] == "recibido"
    assert first_body["customer_status"] == "confirmado"
    assert first_body["promised_ready_by"]
    assert product_service.get_stock(product_id) == 2

    second = client.post(
        "/checkout/pickup/confirm",
        headers={**headers, "Idempotency-Key": "idem-checkout-1"},
        json=payload,
    )
    assert second.status_code == 201
    second_body = second.json()
    assert second_body["order_id"] == first_body["order_id"]
    assert product_service.get_stock(product_id) == 2

    order = client.get(f"/orders/{first_body['order_id']}", headers=headers)
    assert order.status_code == 200
    assert order.json()["state"] == "recibido"
    assert order.json()["customer_status"] == "confirmado"
    assert order.json()["transitions"] == []


def test_pickup_checkout_rejects_when_stock_insufficient_and_rolls_back() -> None:
    headers = _auth_header(roles=["cajero"])
    product_id = _create_product(sku="SKU-CHK-2", stock=1)

    response = client.post(
        "/checkout/pickup/confirm",
        headers={**headers, "Idempotency-Key": "idem-checkout-2"},
        json={
            "branch_id": "br-001",
            "pickup_slot_id": "slot-10-11",
            "customer": {"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
            "lines": [{"product_id": product_id, "qty": 2}],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "INSUFFICIENT_STOCK_AT_CONFIRMATION"
    assert product_service.get_stock(product_id) == 1


def test_order_transitions_follow_state_machine_and_are_auditable() -> None:
    headers = _auth_header(roles=["cajero"])
    order_id = _create_pickup_order(idempotency_key="idem-transition")

    to_prepared = client.post(
        f"/orders/{order_id}/transitions",
        headers=headers,
        json={"target_state": "preparado", "reason": "pedido armado"},
    )
    assert to_prepared.status_code == 200
    assert to_prepared.json()["previous_state"] == "recibido"
    assert to_prepared.json()["current_state"] == "preparado"
    assert to_prepared.json()["customer_status"] == "en_preparacion"

    invalid_jump = client.post(
        f"/orders/{order_id}/transitions",
        headers=headers,
        json={"target_state": "entregado", "reason": "intento salto"},
    )
    assert invalid_jump.status_code == 409
    assert invalid_jump.json()["detail"] == "INVALID_ORDER_TRANSITION"

    to_ready = client.post(
        f"/orders/{order_id}/transitions",
        headers=headers,
        json={"target_state": "listo_para_retiro", "reason": "pedido disponible"},
    )
    assert to_ready.status_code == 200

    to_delivered = client.post(
        f"/orders/{order_id}/transitions",
        headers=headers,
        json={"target_state": "entregado", "reason": "retiro cliente"},
    )
    assert to_delivered.status_code == 200

    same_state = client.post(
        f"/orders/{order_id}/transitions",
        headers=headers,
        json={"target_state": "entregado", "reason": "duplicado"},
    )
    assert same_state.status_code == 409
    assert same_state.json()["detail"] == "ORDER_ALREADY_IN_TARGET_STATE"

    fetched = client.get(f"/orders/{order_id}", headers=headers)
    assert fetched.status_code == 200
    payload = fetched.json()
    assert payload["state"] == "entregado"
    assert payload["customer_status"] == "entregado"
    assert payload["delivered_at"] is not None
    assert [item["current_state"] for item in payload["transitions"]] == [
        "preparado",
        "listo_para_retiro",
        "entregado",
    ]


def test_order_observability_and_consistency_endpoints() -> None:
    headers = _auth_header(roles=["cajero"])
    product_id = _create_product(sku="SKU-MET-1", stock=3)

    checkout = client.post(
        "/checkout/pickup/confirm",
        headers={**headers, "Idempotency-Key": "idem-metrics-1"},
        json={
            "branch_id": "br-001",
            "pickup_slot_id": "slot-10-11",
            "customer": {"name": "Maria", "email": "maria@example.com", "phone": "+56911112222"},
            "lines": [{"product_id": product_id, "qty": 1}],
        },
    )
    assert checkout.status_code == 201
    order_id = checkout.json()["order_id"]

    # generate one rejected transition for observability counters
    rejected = client.post(
        f"/orders/{order_id}/transitions",
        headers=headers,
        json={"target_state": "entregado", "reason": "salto"},
    )
    assert rejected.status_code == 409

    metrics = client.get("/orders/observability/metrics", headers=headers)
    assert metrics.status_code == 200
    body = metrics.json()
    assert body["total_orders"] >= 1
    assert body["states"]["recibido"] >= 1
    assert body["rejected_transitions"] >= 1
    assert body["ready_over_sla"] >= 0

    report = client.get("/orders/consistency/report", headers=headers)
    assert report.status_code == 200
    report_body = report.json()
    assert report_body["total_orders"] >= 1
    assert report_body["orders_with_inconsistencies"] == 0
