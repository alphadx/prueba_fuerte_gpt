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


def _auth_header(*, roles: list[str], sub: str = "user-1") -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(sub=sub, roles=roles)}"}


def test_pickup_web_to_store_e2e_flow() -> None:
    admin = _auth_header(roles=["admin"], sub="admin-1")
    staff = _auth_header(roles=["cajero"], sub="staff-1")

    created = client.post(
        "/products",
        json={"sku": "E2E-001", "name": "Cafe 250g", "price": 4990},
        headers=admin,
    )
    assert created.status_code == 201
    product_id = created.json()["id"]
    product_service.set_stock(product_id, 3)

    catalog = client.get("/catalog/products", params={"branch_id": "br-001"}, headers=staff)
    assert catalog.status_code == 200
    assert any(item["product_id"] == product_id for item in catalog.json()["items"])

    slots = client.get(
        "/pickup-slots",
        params={"branch_id": "br-001", "date": "2026-03-16"},
        headers=staff,
    )
    assert slots.status_code == 200
    slot_id = slots.json()["slots"][0]["pickup_slot_id"]

    checkout = client.post(
        "/checkout/pickup/confirm",
        headers={**staff, "Idempotency-Key": "e2e-idem-001"},
        json={
            "branch_id": "br-001",
            "pickup_slot_id": slot_id,
            "customer": {
                "name": "Cliente Demo",
                "email": "cliente@example.com",
                "phone": "+56999999999",
            },
            "lines": [{"product_id": product_id, "qty": 1}],
        },
    )
    assert checkout.status_code == 201
    order_id = checkout.json()["order_id"]
    assert checkout.json()["order_state"] == "recibido"
    assert checkout.json()["customer_status"] == "confirmado"

    to_prepared = client.post(
        f"/orders/{order_id}/transitions",
        headers=staff,
        json={"target_state": "preparado", "reason": "bodega confirmada"},
    )
    assert to_prepared.status_code == 200

    to_ready = client.post(
        f"/orders/{order_id}/transitions",
        headers=staff,
        json={"target_state": "listo_para_retiro", "reason": "pedido listo en mostrador"},
    )
    assert to_ready.status_code == 200

    to_delivered = client.post(
        f"/orders/{order_id}/transitions",
        headers=staff,
        json={"target_state": "entregado", "reason": "cliente retiró"},
    )
    assert to_delivered.status_code == 200

    final_state = client.get(f"/orders/{order_id}", headers=staff)
    assert final_state.status_code == 200
    payload = final_state.json()
    assert payload["state"] == "entregado"
    assert payload["customer_status"] == "entregado"
    assert [event["current_state"] for event in payload["transitions"]] == [
        "preparado",
        "listo_para_retiro",
        "entregado",
    ]
    assert product_service.get_stock(product_id) == 2
