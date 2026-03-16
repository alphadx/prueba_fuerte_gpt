import pytest

pytest.importorskip("httpx")

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.modules.alerts.notifications import alert_notification_service
from app.modules.alerts.service import alarm_event_service
from app.modules.document_types.service import document_type_service
from app.modules.employee_documents.service import employee_document_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_HS256_SECRET", "test-secret")
    monkeypatch.delenv("JWT_ALLOW_INSECURE_TOKENS", raising=False)
    alarm_event_service.reset_state()
    alert_notification_service.reset_state()
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


def test_alerts_end_to_end_happy_path_summary() -> None:
    headers = _auth_header(roles=["rrhh"])

    eval_response = client.post("/alerts/evaluate", json={"evaluation_date": "2025-01-24"}, headers=headers)
    assert eval_response.status_code == 200
    assert eval_response.json()["generated"] == 1

    dispatch_response = client.post("/alerts/dispatch-pending", headers=headers)
    assert dispatch_response.status_code == 200
    dispatch = dispatch_response.json()
    assert dispatch["processed_events"] == 1
    assert dispatch["sent_attempts"] == 2
    assert dispatch["failed_attempts"] == 0

    summary = client.get("/alerts/summary", headers=headers)
    assert summary.status_code == 200
    summary_body = summary.json()
    assert summary_body["total_events"] == 1
    assert summary_body["sent_events"] == 1
    assert summary_body["failed_events"] == 0
    assert summary_body["total_notification_attempts"] == 2


def test_alerts_dispatch_pending_tolerates_channel_failure_and_allows_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _auth_header(roles=["rrhh"])
    client.post("/alerts/evaluate", json={"evaluation_date": "2025-01-24"}, headers=headers)

    original = alert_notification_service._deliver

    def _patched_deliver(*, channel: str, event):
        if channel == "email":
            return "failed", "simulated email outage"
        return original(channel=channel, event=event)

    monkeypatch.setattr(alert_notification_service, "_deliver", _patched_deliver)

    first_dispatch = client.post("/alerts/dispatch-pending", headers=headers)
    assert first_dispatch.status_code == 200
    first_body = first_dispatch.json()
    assert first_body["processed_events"] == 1
    assert first_body["sent_attempts"] == 1
    assert first_body["failed_attempts"] == 1

    events_after_first = client.get("/alerts/events", headers=headers).json()["items"]
    assert events_after_first[0]["status"] == "partially_failed"
    assert events_after_first[0]["notification_statuses"] == {"in_app": "sent", "email": "failed"}

    monkeypatch.setattr(alert_notification_service, "_deliver", original)
    second_dispatch = client.post("/alerts/dispatch-pending", headers=headers)
    assert second_dispatch.status_code == 200
    second_body = second_dispatch.json()
    assert second_body["processed_events"] == 1
    assert second_body["sent_attempts"] == 1
    assert second_body["failed_attempts"] == 0

    events_after_second = client.get("/alerts/events", headers=headers).json()["items"]
    assert events_after_second[0]["status"] == "sent"
    assert events_after_second[0]["notification_statuses"] == {"in_app": "sent", "email": "sent"}

    attempts = client.get("/alerts/notifications", headers=headers).json()["items"]
    assert len(attempts) == 3


def test_alerts_evaluations_list_for_rrhh() -> None:
    headers = _auth_header(roles=["rrhh"])
    client.post("/alerts/evaluate", json={"evaluation_date": "2025-01-24"}, headers=headers)

    response = client.get("/alerts/evaluations", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["evaluation_date"] == "2025-01-24"


def test_alerts_events_forbidden_for_cajero() -> None:
    response = client.get("/alerts/events", headers=_auth_header(roles=["cajero"]))
    assert response.status_code == 403
