import base64
import json

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _token(*, sub: str, roles: list[str]) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"sub": sub, "roles": roles}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def _auth_header(*, roles: list[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(sub='user-1', roles=roles)}"}


def test_products_requires_authentication() -> None:
    response = client.get('/products')

    assert response.status_code == 401


def test_products_forbid_cajero_create() -> None:
    response = client.post(
        '/products',
        json={"sku": "A1", "name": "Azúcar", "price": 1000},
        headers=_auth_header(roles=["cajero"]),
    )

    assert response.status_code == 403


def test_products_crud_flow_for_admin() -> None:
    headers = _auth_header(roles=["admin"])

    create_response = client.post(
        '/products',
        json={"sku": "SKU-100", "name": "Arroz", "price": 1590},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    list_response = client.get('/products', headers=headers)
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
