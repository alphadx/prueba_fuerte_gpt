import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.alerts.service import alarm_event_service
from app.modules.document_types.service import document_type_service
from app.modules.employee_documents.service import employee_document_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    alarm_event_service.reset_state()
    employee_document_service.reset_state()
    document_type_service.reset_state()

    document_type_service.create_document_type(
        code="LIC",
        name="Licencia",
        requires_expiry=True,
        is_active=True,
        schema_version=1,
        metadata_schema={
            "type": "object",
            "properties": {"issuer": {"type": "string"}},
            "required": ["issuer"],
        },
    )

    employee_document_service.create_document(
        employee_id="emp-001",
        document_type_code="LIC",
        issue_on="2025-01-01",
        expires_on="2025-01-31",
        status="vigente",
        metadata={"issuer": "municipalidad"},
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


def test_alerts_evaluate_for_rrhh_and_idempotent_per_window() -> None:
    headers = _auth_header(roles=["rrhh"])

    first = client.post("/alerts/evaluate", json={"evaluation_date": "2025-01-24"}, headers=headers)
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["generated"] == 1
    assert first_body["queued"] == 1
    assert first_body["items"][0]["threshold_days"] == 7

    second = client.post("/alerts/evaluate", json={"evaluation_date": "2025-01-24"}, headers=headers)
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["generated"] == 0
    assert second_body["queued"] == 0


def test_alerts_events_forbidden_for_cajero() -> None:
    response = client.get("/alerts/events", headers=_auth_header(roles=["cajero"]))
    assert response.status_code == 403
