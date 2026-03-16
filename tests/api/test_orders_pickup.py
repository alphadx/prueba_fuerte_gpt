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
