import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.users.service import user_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    user_service.reset_state()


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


def test_users_forbid_non_rrhh_or_admin_listing() -> None:
    response = client.get("/users", headers=_auth_header(roles=["cajero"]))

    assert response.status_code == 403


def test_users_crud_flow_for_admin() -> None:
    headers = _auth_header(roles=["admin"])

    create_response = client.post(
        "/users",
        json={"username": "jdoe", "full_name": "John Doe", "role": "cajero", "is_active": True},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    list_response = client.get("/users", headers=_auth_header(roles=["rrhh"]))
    assert list_response.status_code == 200
    assert any(item["id"] == created["id"] for item in list_response.json()["items"])

    patch_response = client.patch(
        f"/users/{created['id']}",
        json={"role": "bodega", "is_active": False},
        headers=headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["role"] == "bodega"
    assert patch_response.json()["is_active"] is False

    delete_response = client.delete(f"/users/{created['id']}", headers=headers)
    assert delete_response.status_code == 204


def test_users_reject_duplicate_username() -> None:
    headers = _auth_header(roles=["admin"])
    first = client.post(
        "/users",
        json={"username": "jdoe", "full_name": "John Doe", "role": "cajero", "is_active": True},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/users",
        json={"username": "jdoe", "full_name": "Jane Doe", "role": "rrhh", "is_active": True},
        headers=headers,
    )
    assert duplicate.status_code == 409
