import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.payments.service import payment_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    payment_service.reset_state()


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


def test_payments_forbid_bodega_listing() -> None:
    response = client.get("/payments", headers=_auth_header(roles=["bodega"]))
    assert response.status_code == 403


def test_payments_crud_flow_for_cajero() -> None:
    cajero_headers = _auth_header(roles=["cajero"])
    admin_headers = _auth_header(roles=["admin"])

    create_response = client.post(
        "/payments",
        json={
            "sale_id": "sale-001",
            "amount": 15990,
            "method": "efectivo",
            "status": "pending",
            "idempotency_key": "idem-001",
        },
        headers=cajero_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    list_response = client.get("/payments", headers=cajero_headers)
    assert list_response.status_code == 200
    assert any(item["id"] == created["id"] for item in list_response.json()["items"])

    patch_response = client.patch(
        f"/payments/{created['id']}",
        json={"status": "paid"},
        headers=cajero_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "paid"

    forbidden_delete = client.delete(f"/payments/{created['id']}", headers=cajero_headers)
    assert forbidden_delete.status_code == 403

    allowed_delete = client.delete(f"/payments/{created['id']}", headers=admin_headers)
    assert allowed_delete.status_code == 204


def test_payments_reject_duplicate_idempotency_key() -> None:
    headers = _auth_header(roles=["cajero"])

    first = client.post(
        "/payments",
        json={
            "sale_id": "sale-001",
            "amount": 15990,
            "method": "efectivo",
            "status": "pending",
            "idempotency_key": "idem-001",
        },
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/payments",
        json={
            "sale_id": "sale-001",
            "amount": 15990,
            "method": "efectivo",
            "status": "pending",
            "idempotency_key": "idem-001",
        },
        headers=headers,
    )
    assert second.status_code == 409


def test_cash_payment_endpoint_and_reconciliation() -> None:
    headers = _auth_header(roles=["cajero"])

    create_response = client.post(
        "/payments/cash",
        json={
            "sale_id": "sale-cash-001",
            "company_id": "comp-001",
            "branch_id": "branch-001",
            "channel": "pos",
            "amount": 17000,
            "currency": "CLP",
            "idempotency_key": "idem-cash-001",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["method"] == "cash"
    assert create_response.json()["status"] == "approved"

    reconciliation = client.get("/payments/cash/reconciliation/branch-001", headers=headers)
    assert reconciliation.status_code == 200
    body = reconciliation.json()
    assert body["branch_id"] == "branch-001"
    assert body["payments_total"] == 1
    assert body["approved_total"] == 1
    assert body["pending_total"] == 0
    assert body["amount_total"] == 17000


def test_stub_payment_endpoints_for_transbank_and_mercadopago() -> None:
    headers = _auth_header(roles=["cajero"])

    for provider, idem in [("transbank_stub", "idem-tbk-001"), ("mercadopago_stub", "idem-mp-001")]:
        response = client.post(
            f"/payments/stubs/{provider}",
            json={
                "sale_id": f"sale-{provider}",
                "company_id": "comp-001",
                "branch_id": "branch-001",
                "channel": "web",
                "amount": 21000,
                "currency": "CLP",
                "idempotency_key": idem,
                "metadata": {},
            },
            headers=headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["method"] == provider
        assert body["status"] == "approved"


def test_stub_payment_rejects_unsupported_provider() -> None:
    headers = _auth_header(roles=["cajero"])
    response = client.post(
        "/payments/stubs/bogus",
        json={
            "sale_id": "sale-bogus",
            "company_id": "comp-001",
            "branch_id": "branch-001",
            "channel": "web",
            "amount": 21000,
            "currency": "CLP",
            "idempotency_key": "idem-bogus-001",
            "metadata": {},
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_webhook_endpoint_idempotent_and_signature_checked() -> None:
    headers = _auth_header(roles=["cajero"])

    created = client.post(
        "/payments/stubs/transbank_stub",
        json={
            "sale_id": "sale-webhook-1",
            "company_id": "comp-001",
            "branch_id": "branch-001",
            "channel": "web",
            "amount": 20000,
            "currency": "CLP",
            "idempotency_key": "idem-webhook-001",
            "metadata": {},
        },
        headers=headers,
    )
    assert created.status_code == 201

    first = client.post(
        "/payments/webhooks/transbank_stub",
        json={
            "signature": "transbank_stub:test",
            "payload": {
                "event_id": "evt-webhook-1",
                "idempotency_key": "idem-webhook-001",
                "provider_payment_id": "transbank_stub-idem-webhook-001",
                "status": "reconciled",
            },
        },
        headers=headers,
    )
    assert first.status_code == 200
    assert first.json()["duplicated"] is False
    assert first.json()["current_status"] == "reconciled"

    second = client.post(
        "/payments/webhooks/transbank_stub",
        json={
            "signature": "transbank_stub:test",
            "payload": {
                "event_id": "evt-webhook-1",
                "idempotency_key": "idem-webhook-001",
                "provider_payment_id": "transbank_stub-idem-webhook-001",
                "status": "reconciled",
            },
        },
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json()["duplicated"] is True

    invalid_signature = client.post(
        "/payments/webhooks/transbank_stub",
        json={
            "signature": "bad",
            "payload": {
                "event_id": "evt-webhook-2",
                "provider_payment_id": "transbank_stub-idem-webhook-001",
                "status": "approved",
            },
        },
        headers=headers,
    )
    assert invalid_signature.status_code == 401


def test_payment_flags_by_branch_channel_block_and_allow() -> None:
    admin = _auth_header(roles=["admin"])
    cajero = _auth_header(roles=["cajero"])

    set_flag = client.put(
        "/payments/flags",
        json={"branch_id": "branch-777", "channel": "web", "method": "transbank_stub", "enabled": False},
        headers=admin,
    )
    assert set_flag.status_code == 200
    assert set_flag.json()["enabled"] is False

    blocked = client.post(
        "/payments/stubs/transbank_stub",
        json={
            "sale_id": "sale-flag-1",
            "company_id": "comp-001",
            "branch_id": "branch-777",
            "channel": "web",
            "amount": 18000,
            "currency": "CLP",
            "idempotency_key": "idem-flag-1",
            "metadata": {},
        },
        headers=cajero,
    )
    assert blocked.status_code == 403

    enable_flag = client.put(
        "/payments/flags",
        json={"branch_id": "branch-777", "channel": "web", "method": "transbank_stub", "enabled": True},
        headers=admin,
    )
    assert enable_flag.status_code == 200

    allowed = client.post(
        "/payments/stubs/transbank_stub",
        json={
            "sale_id": "sale-flag-2",
            "company_id": "comp-001",
            "branch_id": "branch-777",
            "channel": "web",
            "amount": 18000,
            "currency": "CLP",
            "idempotency_key": "idem-flag-2",
            "metadata": {},
        },
        headers=cajero,
    )
    assert allowed.status_code == 201


def test_stub_integral_reject_timeout_and_duplicate_idempotency() -> None:
    headers = _auth_header(roles=["cajero"])

    rejected = client.post(
        "/payments/stubs/transbank_stub",
        json={
            "sale_id": "sale-reject-1",
            "company_id": "comp-001",
            "branch_id": "branch-001",
            "channel": "web",
            "amount": 12000,
            "currency": "CLP",
            "idempotency_key": "idem-reject-1",
            "metadata": {"force_reject": "true"},
        },
        headers=headers,
    )
    assert rejected.status_code == 201
    assert rejected.json()["status"] == "rejected"

    timeout = client.post(
        "/payments/stubs/mercadopago_stub",
        json={
            "sale_id": "sale-timeout-1",
            "company_id": "comp-001",
            "branch_id": "branch-001",
            "channel": "web",
            "amount": 12000,
            "currency": "CLP",
            "idempotency_key": "idem-timeout-1",
            "metadata": {"force_timeout": "true"},
        },
        headers=headers,
    )
    assert timeout.status_code == 201
    assert timeout.json()["status"] == "rejected"

    first = client.post(
        "/payments/stubs/transbank_stub",
        json={
            "sale_id": "sale-dup-1",
            "company_id": "comp-001",
            "branch_id": "branch-001",
            "channel": "web",
            "amount": 12000,
            "currency": "CLP",
            "idempotency_key": "idem-dup-1",
            "metadata": {},
        },
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/payments/stubs/transbank_stub",
        json={
            "sale_id": "sale-dup-1",
            "company_id": "comp-001",
            "branch_id": "branch-001",
            "channel": "web",
            "amount": 12000,
            "currency": "CLP",
            "idempotency_key": "idem-dup-1",
            "metadata": {},
        },
        headers=headers,
    )
    assert duplicate.status_code == 409


def test_payments_observability_metrics_endpoint() -> None:
    headers = _auth_header(roles=["cajero"])

    create_pending = client.post(
        "/payments",
        json={
            "sale_id": "sale-metrics-1",
            "amount": 10000,
            "method": "efectivo",
            "status": "pending",
            "idempotency_key": "idem-metrics-1",
        },
        headers=headers,
    )
    assert create_pending.status_code == 201

    create_rejected = client.post(
        "/payments",
        json={
            "sale_id": "sale-metrics-2",
            "amount": 12000,
            "method": "efectivo",
            "status": "rejected",
            "idempotency_key": "idem-metrics-2",
        },
        headers=headers,
    )
    assert create_rejected.status_code == 201

    metrics = client.get("/payments/observability/metrics", headers=headers)
    assert metrics.status_code == 200
    body = metrics.json()
    assert body["payments_total"] == 2
    assert body["rejected_total"] == 1
    assert body["pending_total"] == 1
    assert body["error_rate"] == 50.0
