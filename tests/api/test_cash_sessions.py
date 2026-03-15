import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.cash_sessions.service import cash_session_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    cash_session_service.reset_state()


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


def test_cash_sessions_forbid_rrhh_listing() -> None:
    response = client.get("/cash-sessions", headers=_auth_header(roles=["rrhh"]))
    assert response.status_code == 403


def test_cash_sessions_crud_flow_for_cajero() -> None:
    cajero_headers = _auth_header(roles=["cajero"])
    admin_headers = _auth_header(roles=["admin"])

    create_response = client.post(
        "/cash-sessions",
        json={"branch_id": "br-001", "opened_by": "usr-001", "opening_amount": 100000, "status": "open"},
        headers=cajero_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    list_response = client.get("/cash-sessions", headers=cajero_headers)
    assert list_response.status_code == 200
    assert any(item["id"] == created["id"] for item in list_response.json()["items"])

    patch_response = client.patch(
        f"/cash-sessions/{created['id']}",
        json={"closing_amount": 95000, "status": "closed"},
        headers=cajero_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "closed"

    forbidden_delete = client.delete(f"/cash-sessions/{created['id']}", headers=cajero_headers)
    assert forbidden_delete.status_code == 403

    allowed_delete = client.delete(f"/cash-sessions/{created['id']}", headers=admin_headers)
    assert allowed_delete.status_code == 204
