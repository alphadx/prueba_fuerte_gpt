import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.products.service import product_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    product_service.reset_state()


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


def test_products_requires_authentication() -> None:
    response = client.get("/products")

    assert response.status_code == 401


def test_products_forbid_cajero_create() -> None:
    response = client.post(
        "/products",
        json={"sku": "A1", "name": "Azúcar", "price": 1000},
        headers=_auth_header(roles=["cajero"]),
    )

    assert response.status_code == 403


def test_products_reject_invalid_signature() -> None:
    response = client.get(
        "/products",
        headers={"Authorization": f"Bearer {_token(sub='user-1', roles=['admin'], secret='wrong-secret')}"},
    )

    assert response.status_code == 401


def test_products_reject_duplicate_sku() -> None:
    headers = _auth_header(roles=["admin"])

    first = client.post(
        "/products",
        json={"sku": "SKU-100", "name": "Arroz", "price": 1590},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/products",
        json={"sku": "SKU-100", "name": "Arroz Premium", "price": 2090},
        headers=headers,
    )
    assert second.status_code == 409


def test_products_forbid_delete_for_non_admin() -> None:
    admin_headers = _auth_header(roles=["admin"])
    bodega_headers = _auth_header(roles=["bodega"])

    created = client.post(
        "/products",
        json={"sku": "SKU-100", "name": "Arroz", "price": 1590},
        headers=admin_headers,
    )
    product_id = created.json()["id"]

    forbidden = client.delete(f"/products/{product_id}", headers=bodega_headers)
    assert forbidden.status_code == 403


def test_products_crud_flow_for_admin() -> None:
    headers = _auth_header(roles=["admin"])

    create_response = client.post(
        "/products",
        json={"sku": "SKU-100", "name": "Arroz", "price": 1590},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    list_response = client.get("/products", headers=headers)
    assert list_response.status_code == 200
    assert any(item["id"] == created["id"] for item in list_response.json()["items"])

    update_response = client.patch(
        f"/products/{created['id']}",
        json={"name": "Arroz Grado 1"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Arroz Grado 1"

    delete_response = client.delete(f"/products/{created['id']}", headers=headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/products/{created['id']}", headers=headers)
    assert get_response.status_code == 404
