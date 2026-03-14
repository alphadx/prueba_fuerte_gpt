from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_returns_ready() -> None:
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_dispatch_alert_queues_message() -> None:
    client = TestClient(app)

    response = client.post(
        "/alerts/dispatch",
        json={
            "employee_id": "emp-001",
            "document_type": "licencia_conducir",
            "days_to_expire": 7,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["backend"] in {"redis", "memory"}


def test_dispatch_alert_rejects_invalid_payload() -> None:
    client = TestClient(app)

    response = client.post(
        "/alerts/dispatch",
        json={"employee_id": "", "document_type": "", "days_to_expire": -1},
    )

    assert response.status_code == 422
