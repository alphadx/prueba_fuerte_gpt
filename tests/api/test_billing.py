import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.billing.service import billing_service
from app.modules.cash_sessions.service import cash_session_service
from app.modules.products.service import product_service
from app.modules.sales.service import sale_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    monkeypatch.delenv("BILLING_SANDBOX_FORCE_ERROR", raising=False)
    product_service.reset_state()
    cash_session_service.reset_state()
    sale_service.reset_state()
    billing_service.reset_state()


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


def _create_sale(headers_admin: dict[str, str], headers_cajero: dict[str, str]) -> str:
    created_product = client.post(
        "/products",
        json={"sku": "BILL-001", "name": "Pan", "price": 1000},
        headers=headers_admin,
    )
    product_id = created_product.json()["id"]
    product_service.set_stock(product_id, 10)

    opened_session = client.post(
        "/cash-sessions",
        json={"branch_id": "br-001", "opened_by": "usr-001", "opening_amount": 0, "status": "open"},
        headers=headers_cajero,
    )
    session_id = opened_session.json()["id"]

    sale_response = client.post(
        "/sales/complete",
        json={
            "branch_id": "br-001",
            "cash_session_id": session_id,
            "sold_by": "usr-001",
            "payment_method": "cash",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
        headers=headers_cajero,
    )
    assert sale_response.status_code == 201
    return sale_response.json()["id"]


def test_billing_document_status_flow() -> None:
    admin_headers = _auth_header(roles=["admin"])
    cajero_headers = _auth_header(roles=["cajero"])
    sale_id = _create_sale(admin_headers, cajero_headers)

    queued = client.get(f"/billing/documents/{sale_id}", headers=cajero_headers)
    assert queued.status_code == 200
    assert queued.json()["status"] == "queued"

    processed = client.post("/billing/worker/process", json={"limit": 10}, headers=admin_headers)
    assert processed.status_code == 200
    payload_worker = processed.json()
    assert payload_worker["enqueued"] == 1
    assert payload_worker["succeeded"] == 1

    emitted = client.get(f"/billing/documents/{sale_id}", headers=cajero_headers)
    payload = emitted.json()
    assert emitted.status_code == 200
    assert payload["status"] == "accepted"
    assert payload["folio"] is not None
    assert payload["track_id"] is not None
    assert payload["sii_status"] == "accepted"


def test_billing_status_query_returns_404_for_unknown_sale() -> None:
    admin_headers = _auth_header(roles=["admin"])
    not_found = client.get("/billing/documents/sale-404", headers=admin_headers)
    assert not_found.status_code == 404


def test_billing_sale_enqueue_is_async_until_worker_batch() -> None:
    admin_headers = _auth_header(roles=["admin"])
    cajero_headers = _auth_header(roles=["cajero"])
    sale_id = _create_sale(admin_headers, cajero_headers)

    queued = client.get(f"/billing/documents/{sale_id}", headers=cajero_headers)
    assert queued.status_code == 200
    queued_payload = queued.json()
    assert queued_payload["status"] == "queued"
    assert queued_payload["attempts"] == 0
    assert queued_payload["track_id"] is None

    processed = client.post("/billing/worker/process", json={"limit": 10}, headers=admin_headers)
    assert processed.status_code == 200
    assert processed.json()["enqueued"] == 1

    emitted = client.get(f"/billing/documents/{sale_id}", headers=cajero_headers)
    assert emitted.status_code == 200
    assert emitted.json()["attempts"] >= 1
    assert emitted.json()["track_id"] is not None
