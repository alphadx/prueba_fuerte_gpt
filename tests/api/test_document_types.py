import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.document_types.service import document_type_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    document_type_service.reset_state()


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


def test_document_types_forbid_cajero_listing() -> None:
    response = client.get("/document-types", headers=_auth_header(roles=["cajero"]))
    assert response.status_code == 403


def test_document_types_crud_flow_for_rrhh() -> None:
    rrhh_headers = _auth_header(roles=["rrhh"])
    admin_headers = _auth_header(roles=["admin"])

    create_response = client.post(
        "/document-types",
        json={
            "code": "LIC",
            "name": "Licencia Conducir",
            "requires_expiry": True,
            "is_active": True,
            "schema_version": 1,
            "metadata_schema": {
                "type": "object",
                "properties": {"issuer": {"type": "string"}},
                "required": ["issuer"],
            },
        },
        headers=rrhh_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["schema_version"] == 1

    list_response = client.get("/document-types", headers=rrhh_headers)
    assert list_response.status_code == 200
    assert any(item["id"] == created["id"] for item in list_response.json()["items"])

    patch_response = client.patch(
        f"/document-types/{created['id']}",
        json={"name": "Licencia Clase B", "requires_expiry": False, "schema_version": 2},
        headers=rrhh_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Licencia Clase B"
    assert patch_response.json()["schema_version"] == 2

    forbidden_delete = client.delete(f"/document-types/{created['id']}", headers=rrhh_headers)
    assert forbidden_delete.status_code == 403

    allowed_delete = client.delete(f"/document-types/{created['id']}", headers=admin_headers)
    assert allowed_delete.status_code == 204


def test_document_types_reject_duplicate_code() -> None:
    headers = _auth_header(roles=["rrhh"])
    first = client.post(
        "/document-types",
        json={
            "code": "LIC",
            "name": "Licencia Conducir",
            "requires_expiry": True,
            "is_active": True,
            "schema_version": 1,
            "metadata_schema": {"type": "object", "properties": {}, "required": []},
        },
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/document-types",
        json={
            "code": "LIC",
            "name": "Otra Licencia",
            "requires_expiry": False,
            "is_active": True,
            "schema_version": 1,
            "metadata_schema": {"type": "object", "properties": {}, "required": []},
        },
        headers=headers,
    )
    assert second.status_code == 409


def test_document_types_reject_invalid_schema() -> None:
    headers = _auth_header(roles=["rrhh"])
    response = client.post(
        "/document-types",
        json={
            "code": "BAD",
            "name": "Invalido",
            "requires_expiry": True,
            "is_active": True,
            "schema_version": 1,
            "metadata_schema": {"type": "string"},
        },
        headers=headers,
    )
    assert response.status_code == 409
