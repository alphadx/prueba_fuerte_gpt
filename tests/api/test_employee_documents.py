import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.document_types.service import document_type_service
from app.modules.employee_documents.file_storage import employee_document_file_storage_service
from app.modules.employee_documents.service import employee_document_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    employee_document_service.reset_state()
    employee_document_file_storage_service.reset_state()
    document_type_service.reset_state()
    document_type_service.create_document_type(
        code="LIC",
        name="Licencia",
        requires_expiry=True,
        is_active=True,
        schema_version=1,
        metadata_schema={
            "type": "object",
            "properties": {
                "issuer": {"type": "string"},
                "region": {"type": "string"},
            },
            "required": ["issuer"],
        },
    )


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


def test_employee_documents_forbid_cajero_listing() -> None:
    response = client.get("/employee-documents", headers=_auth_header(roles=["cajero"]))
    assert response.status_code == 403


def test_employee_documents_crud_flow_for_rrhh() -> None:
    rrhh_headers = _auth_header(roles=["rrhh"])
    admin_headers = _auth_header(roles=["admin"])

    create_response = client.post(
        "/employee-documents",
        json={
            "employee_id": "emp-001",
            "document_type_code": "LIC",
            "issue_on": "2025-01-01",
            "expires_on": "2027-12-31",
            "status": "vigente",
            "metadata": {"issuer": "municipalidad", "region": "RM"},
        },
        headers=rrhh_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    upload_response = client.post(
        f"/employee-documents/{created['id']}/files",
        json={
            "file_name": "licencia.pdf",
            "content_type": "application/pdf",
            "storage_uri": f"minio://hr/{created['id']}/licencia.pdf",
            "uploaded_at": "2025-01-01T10:00:00Z",
        },
        headers=rrhh_headers,
    )
    assert upload_response.status_code == 201

    files_response = client.get(f"/employee-documents/{created['id']}/files", headers=rrhh_headers)
    assert files_response.status_code == 200
    assert len(files_response.json()["items"]) == 1

    list_response = client.get("/employee-documents", headers=rrhh_headers)
    assert list_response.status_code == 200
    assert any(item["id"] == created["id"] for item in list_response.json()["items"])

    patch_response = client.patch(
        f"/employee-documents/{created['id']}",
        json={"status": "por_vencer", "metadata": {"issuer": "seremi", "region": "RM"}},
        headers=rrhh_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "por_vencer"

    forbidden_delete = client.delete(f"/employee-documents/{created['id']}", headers=rrhh_headers)
    assert forbidden_delete.status_code == 403

    allowed_delete = client.delete(f"/employee-documents/{created['id']}", headers=admin_headers)
    assert allowed_delete.status_code == 204


def test_employee_documents_reject_duplicate_key() -> None:
    headers = _auth_header(roles=["rrhh"])

    first = client.post(
        "/employee-documents",
        json={
            "employee_id": "emp-001",
            "document_type_code": "LIC",
            "issue_on": "2025-01-01",
            "expires_on": "2027-12-31",
            "status": "vigente",
            "metadata": {"issuer": "municipalidad"},
        },
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/employee-documents",
        json={
            "employee_id": "emp-001",
            "document_type_code": "LIC",
            "issue_on": "2025-01-01",
            "expires_on": "2028-01-01",
            "status": "vigente",
            "metadata": {"issuer": "municipalidad"},
        },
        headers=headers,
    )
    assert second.status_code == 409


def test_employee_documents_reject_invalid_metadata() -> None:
    headers = _auth_header(roles=["rrhh"])
    response = client.post(
        "/employee-documents",
        json={
            "employee_id": "emp-002",
            "document_type_code": "LIC",
            "issue_on": "2025-01-01",
            "expires_on": "2027-12-31",
            "status": "vigente",
            "metadata": {"region": "RM"},
        },
        headers=headers,
    )
    assert response.status_code == 422
