"""Carga fixtures críticos de paso 11 sobre API in-memory.

Ejecuta escenarios determinísticos y genera un reporte JSON con sus resultados.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
API_DIR = ROOT_DIR / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from fastapi.testclient import TestClient

from app.main import app
from app.modules.alerts.notifications import alert_notification_service
from app.modules.alerts.service import alarm_event_service
from app.modules.billing.service import billing_service
from app.modules.branches.service import branch_service
from app.modules.cash_sessions.service import cash_session_service
from app.modules.document_types.service import document_type_service
from app.modules.employee_documents.file_storage import employee_document_file_storage_service
from app.modules.employee_documents.service import employee_document_service
from app.modules.employees.service import employee_service
from app.modules.orders.service import pickup_order_service
from app.modules.payments.service import payment_service
from app.modules.products.service import product_service
from app.modules.sales.service import sale_service
from app.modules.users.service import user_service

DEFAULT_OUTPUT_PATH = Path("infra/seeds/fixtures_state.json")


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


def _expect(response_status: int, expected: int, context: str) -> None:
    if response_status != expected:
        raise RuntimeError(f"{context}: esperado={expected} obtenido={response_status}")


def _reset_state() -> None:
    branch_service.reset_state()
    user_service.reset_state()
    product_service.reset_state()
    cash_session_service.reset_state()
    sale_service.reset_state()
    payment_service.reset_state()
    billing_service.reset_state()
    employee_service.reset_state()
    document_type_service.reset_state()
    employee_document_service.reset_state()
    employee_document_file_storage_service.reset_state()
    alarm_event_service.reset_state()
    alert_notification_service.reset_state()
    pickup_order_service.reset_state()


def _fixture_sale_cash(client: TestClient, *, sku: str = "FX-CASH-001") -> dict[str, Any]:
    admin = _auth_header(roles=["admin"], sub="admin-1")
    cajero = _auth_header(roles=["cajero"], sub="cashier-1")

    created = client.post("/products", json={"sku": sku, "name": "Pan Corriente", "price": 1000}, headers=admin)
    _expect(created.status_code, 201, "FX-SALE-CASH/create-product")
    product_id = created.json()["id"]
    product_service.set_stock(product_id, 10)

    opened = client.post(
        "/cash-sessions",
        json={"branch_id": "branch-001", "opened_by": "usr-cajero-001", "opening_amount": 5000, "status": "open"},
        headers=cajero,
    )
    _expect(opened.status_code, 201, "FX-SALE-CASH/open-session")

    sale = client.post(
        "/sales/complete",
        json={
            "branch_id": "branch-001",
            "cash_session_id": opened.json()["id"],
            "sold_by": "usr-cajero-001",
            "payment_method": "cash",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
        headers=cajero,
    )
    _expect(sale.status_code, 201, "FX-SALE-CASH/complete-sale")
    payload = sale.json()
    if payload["status"] != "paid" or payload["payment_status"] != "approved":
        raise RuntimeError("FX-SALE-CASH/sale-status inválido")

    close_session = client.patch(
        f"/cash-sessions/{opened.json()['id']}",
        json={"cash_delta": payload["total"], "closing_amount": 5000 + payload["total"], "status": "closed"},
        headers=cajero,
    )
    _expect(close_session.status_code, 200, "FX-SALE-CASH/close-session")

    return {"sale_id": payload["id"], "product_id": product_id, "status": payload["status"]}


def _fixture_sale_electronic(client: TestClient) -> dict[str, Any]:
    admin = _auth_header(roles=["admin"], sub="admin-1")
    cajero = _auth_header(roles=["cajero"], sub="cashier-1")

    created = client.post("/products", json={"sku": "FX-CARD-001", "name": "Bebida", "price": 1500}, headers=admin)
    _expect(created.status_code, 201, "FX-SALE-ELECTRONIC/create-product")
    product_id = created.json()["id"]
    product_service.set_stock(product_id, 5)

    opened = client.post(
        "/cash-sessions",
        json={"branch_id": "branch-001", "opened_by": "usr-cajero-001", "opening_amount": 0, "status": "open"},
        headers=cajero,
    )
    _expect(opened.status_code, 201, "FX-SALE-ELECTRONIC/open-session")

    sale = client.post(
        "/sales/complete",
        json={
            "branch_id": "branch-001",
            "cash_session_id": opened.json()["id"],
            "sold_by": "usr-cajero-001",
            "payment_method": "card_stub",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
        headers=cajero,
    )
    _expect(sale.status_code, 201, "FX-SALE-ELECTRONIC/complete-sale")
    payload = sale.json()
    if payload["status"] != "confirmed":
        raise RuntimeError("FX-SALE-ELECTRONIC/status inválido")

    close_session = client.patch(
        f"/cash-sessions/{opened.json()['id']}",
        json={"cash_delta": 0, "closing_amount": 0, "status": "closed"},
        headers=cajero,
    )
    _expect(close_session.status_code, 200, "FX-SALE-ELECTRONIC/close-session")

    return {"sale_id": payload["id"], "status": payload["status"], "payment_status": payload["payment_status"]}


def _fixture_web_pickup(client: TestClient) -> dict[str, Any]:
    admin = _auth_header(roles=["admin"], sub="admin-1")
    staff = _auth_header(roles=["cajero"], sub="staff-1")

    created = client.post("/products", json={"sku": "FX-WEB-001", "name": "Café", "price": 4900}, headers=admin)
    _expect(created.status_code, 201, "FX-WEB-PICKUP/create-product")
    product_id = created.json()["id"]
    product_service.set_stock(product_id, 3)

    slots = client.get("/pickup-slots", params={"branch_id": "br-001", "date": "2026-03-16"}, headers=staff)
    _expect(slots.status_code, 200, "FX-WEB-PICKUP/get-slots")
    slot_id = slots.json()["slots"][0]["pickup_slot_id"]

    checkout = client.post(
        "/checkout/pickup/confirm",
        headers={**staff, "Idempotency-Key": "fx-web-pickup-001"},
        json={
            "branch_id": "br-001",
            "pickup_slot_id": slot_id,
            "customer": {"name": "Cliente Fixture", "email": "fixture@example.com", "phone": "+56999999999"},
            "lines": [{"product_id": product_id, "qty": 1}],
        },
    )
    _expect(checkout.status_code, 201, "FX-WEB-PICKUP/checkout")
    payload = checkout.json()
    if payload["order_state"] != "recibido":
        raise RuntimeError("FX-WEB-PICKUP/order_state inválido")
    return {"order_id": payload["order_id"], "state": payload["order_state"]}


def _fixture_billing_sandbox(client: TestClient) -> dict[str, Any]:
    admin = _auth_header(roles=["admin"], sub="admin-1")
    cajero = _auth_header(roles=["cajero"], sub="cashier-1")

    cash_sale = _fixture_sale_cash(client, sku="FX-BILLING-CASH-001")
    sale_id = cash_sale["sale_id"]

    processed = client.post("/billing/worker/process", json={"limit": 10}, headers=admin)
    _expect(processed.status_code, 200, "FX-BILLING-SBX/worker-process")

    doc = client.get(f"/billing/documents/{sale_id}", headers=cajero)
    _expect(doc.status_code, 200, "FX-BILLING-SBX/get-document")
    payload = doc.json()
    if payload["status"] not in {"accepted", "queued"}:
        raise RuntimeError("FX-BILLING-SBX/status inesperado")
    return {"sale_id": sale_id, "document_status": payload["status"], "track_id": payload.get("track_id")}


def _fixture_payment_webhook(client: TestClient) -> dict[str, Any]:
    cajero = _auth_header(roles=["cajero"], sub="cashier-1")

    created = client.post(
        "/payments/stubs/transbank_stub",
        json={
            "sale_id": "fx-webhook-sale-001",
            "company_id": "comp-001",
            "branch_id": "branch-001",
            "channel": "web",
            "amount": 20000,
            "currency": "CLP",
            "idempotency_key": "fx-webhook-idem-001",
            "metadata": {},
        },
        headers=cajero,
    )
    _expect(created.status_code, 201, "FX-PAYMENT-WEBHOOK/create-payment")

    first = client.post(
        "/payments/webhooks/transbank_stub",
        json={
            "signature": "transbank_stub:test",
            "payload": {
                "event_id": "fx-event-001",
                "idempotency_key": "fx-webhook-idem-001",
                "provider_payment_id": "transbank_stub-fx-webhook-idem-001",
                "status": "reconciled",
            },
        },
        headers=cajero,
    )
    _expect(first.status_code, 200, "FX-PAYMENT-WEBHOOK/first-webhook")
    first_payload = first.json()

    second = client.post(
        "/payments/webhooks/transbank_stub",
        json={
            "signature": "transbank_stub:test",
            "payload": {
                "event_id": "fx-event-001",
                "idempotency_key": "fx-webhook-idem-001",
                "provider_payment_id": "transbank_stub-fx-webhook-idem-001",
                "status": "reconciled",
            },
        },
        headers=cajero,
    )
    _expect(second.status_code, 200, "FX-PAYMENT-WEBHOOK/second-webhook")

    payload = second.json()
    if payload.get("duplicated") is not True:
        raise RuntimeError("FX-PAYMENT-WEBHOOK/no detecta duplicado")
    return {"event_id": "fx-event-001", "duplicated": payload["duplicated"], "status": first_payload.get("current_status")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga fixtures críticos de paso 11")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Ruta para reporte JSON de fixtures")
    args = parser.parse_args()

    os.environ.setdefault("JWT_HS256_SECRET", "test-secret")
    os.environ.setdefault("ALLOW_MEMORY_QUEUE_FALLBACK", "true")

    _reset_state()
    client = TestClient(app)

    results: dict[str, Any] = {
        "fixtures": {
            "FX-SALE-CASH": _fixture_sale_cash(client),
            "FX-SALE-ELECTRONIC": _fixture_sale_electronic(client),
            "FX-WEB-PICKUP": _fixture_web_pickup(client),
            "FX-BILLING-SBX": _fixture_billing_sandbox(client),
            "FX-PAYMENT-WEBHOOK": _fixture_payment_webhook(client),
        }
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Fixtures críticos cargados y reportados en {output_path}")


if __name__ == "__main__":
    main()
