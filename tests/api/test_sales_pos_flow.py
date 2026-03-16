import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.cash_sessions.service import cash_session_service
from app.modules.products.service import product_service
from app.modules.sales.service import sale_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.setenv("ALLOW_MEMORY_QUEUE_FALLBACK", "true")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    product_service.reset_state()
    cash_session_service.reset_state()
    sale_service.reset_state()


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


def test_pos_complete_sale_cash_and_close_session() -> None:
    admin_headers = _auth_header(roles=["admin"])
    cajero_headers = _auth_header(roles=["cajero"])

    created_product = client.post(
        "/products",
        json={"sku": "POS-001", "name": "Pan", "price": 1000},
        headers=admin_headers,
    )
    assert created_product.status_code == 201
    product_id = created_product.json()["id"]
    product_service.set_stock(product_id, 10)

    opened_session = client.post(
        "/cash-sessions",
        json={"branch_id": "br-001", "opened_by": "usr-001", "opening_amount": 50000, "status": "open"},
        headers=cajero_headers,
    )
    assert opened_session.status_code == 201
    session_id = opened_session.json()["id"]

    sale_response = client.post(
        "/sales/complete",
        json={
            "branch_id": "br-001",
            "cash_session_id": session_id,
            "sold_by": "usr-001",
            "payment_method": "cash",
            "lines": [{"product_id": product_id, "quantity": 2}],
        },
        headers=cajero_headers,
    )
    assert sale_response.status_code == 201
    sale = sale_response.json()
    assert sale["status"] == "paid"
    assert sale["payment_status"] == "approved"
    assert sale["subtotal"] == 2000.0
    assert sale["taxes"] == 380.0
    assert sale["total"] == 2380.0
    assert sale["billing_event_emitted"] is True

    assert product_service.get_stock(product_id) == 8
    assert any(m.reference_id == sale["id"] for m in product_service.list_stock_movements())

    session_update = client.patch(
        f"/cash-sessions/{session_id}",
        json={"cash_delta": sale["total"], "closing_amount": 52380, "status": "closed"},
        headers=cajero_headers,
    )
    assert session_update.status_code == 200
    updated_session = session_update.json()
    assert updated_session["status"] == "closed"
    assert updated_session["expected_amount"] == 52380
    assert updated_session["difference_amount"] == 0


def test_pos_rolls_back_when_stock_is_insufficient() -> None:
    admin_headers = _auth_header(roles=["admin"])
    cajero_headers = _auth_header(roles=["cajero"])

    created_product = client.post(
        "/products",
        json={"sku": "POS-002", "name": "Leche", "price": 1200},
        headers=admin_headers,
    )
    product_id = created_product.json()["id"]
    product_service.set_stock(product_id, 1)

    opened_session = client.post(
        "/cash-sessions",
        json={"branch_id": "br-001", "opened_by": "usr-001", "opening_amount": 0, "status": "open"},
        headers=cajero_headers,
    )
    session_id = opened_session.json()["id"]

    sale_response = client.post(
        "/sales/complete",
        json={
            "branch_id": "br-001",
            "cash_session_id": session_id,
            "sold_by": "usr-001",
            "payment_method": "cash",
            "lines": [{"product_id": product_id, "quantity": 2}],
        },
        headers=cajero_headers,
    )
    assert sale_response.status_code == 409
    assert product_service.get_stock(product_id) == 1
    assert sale_service.list_sales() == []


def test_pos_card_stub_keeps_sale_confirmed_and_payment_pending() -> None:
    admin_headers = _auth_header(roles=["admin"])
    cajero_headers = _auth_header(roles=["cajero"])

    created_product = client.post(
        "/products",
        json={"sku": "POS-003", "name": "Bebida", "price": 1500},
        headers=admin_headers,
    )
    assert created_product.status_code == 201
    product_id = created_product.json()["id"]
    product_service.set_stock(product_id, 5)

    opened_session = client.post(
        "/cash-sessions",
        json={"branch_id": "br-001", "opened_by": "usr-001", "opening_amount": 0, "status": "open"},
        headers=cajero_headers,
    )
    assert opened_session.status_code == 201

    sale_response = client.post(
        "/sales/complete",
        json={
            "branch_id": "br-001",
            "cash_session_id": opened_session.json()["id"],
            "sold_by": "usr-001",
            "payment_method": "card_stub",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
        headers=cajero_headers,
    )
    assert sale_response.status_code == 201
    sale = sale_response.json()
    assert sale["status"] == "confirmed"
    assert sale["payment_status"] == "pending"
    assert sale["billing_event_emitted"] is True


def test_pos_rejects_sale_when_cash_session_branch_mismatch() -> None:
    admin_headers = _auth_header(roles=["admin"])
    cajero_headers = _auth_header(roles=["cajero"])

    created_product = client.post(
        "/products",
        json={"sku": "POS-004", "name": "Queso", "price": 2500},
        headers=admin_headers,
    )
    assert created_product.status_code == 201
    product_id = created_product.json()["id"]
    product_service.set_stock(product_id, 5)

    opened_session = client.post(
        "/cash-sessions",
        json={"branch_id": "br-001", "opened_by": "usr-001", "opening_amount": 0, "status": "open"},
        headers=cajero_headers,
    )
    assert opened_session.status_code == 201

    sale_response = client.post(
        "/sales/complete",
        json={
            "branch_id": "br-999",
            "cash_session_id": opened_session.json()["id"],
            "sold_by": "usr-001",
            "payment_method": "cash",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
        headers=cajero_headers,
    )
    assert sale_response.status_code == 409
    assert "branch mismatch" in sale_response.json()["detail"]
