from app.modules.alerts.service import alarm_event_service
from app.modules.employee_documents.service import employee_document_service


def setup_function() -> None:
    alarm_event_service.reset_state()
    employee_document_service.reset_state()


def test_alerts_service_generates_threshold_events_and_is_idempotent() -> None:
    doc = employee_document_service.create_document(
        employee_id="emp-001",
        document_type_code="LIC",
        issue_on="2025-01-01",
        expires_on="2025-01-31",
        status="vigente",
        metadata={"issuer": "municipalidad"},
    )

    first = alarm_event_service.evaluate_documents(documents=[doc], evaluation_date="2025-01-24")
    assert len(first.events) == 1
    assert first.events[0].threshold_days == 7
    assert first.events[0].dedupe_key == f"{doc.id}:7:2025-01-24"
    assert first.run.generated_events == 1
    assert first.run.duplicate_events == 0

    second = alarm_event_service.evaluate_documents(documents=[doc], evaluation_date="2025-01-24")
    assert len(second.events) == 0
    assert second.run.generated_events == 0
    assert second.run.duplicate_events == 1


def test_alerts_service_tracks_expired_and_non_threshold_documents() -> None:
    doc1 = employee_document_service.create_document(
        employee_id="emp-001",
        document_type_code="LIC",
        issue_on="2025-01-01",
        expires_on="2025-01-20",
        status="vigente",
        metadata={"issuer": "municipalidad"},
    )
    doc2 = employee_document_service.create_document(
        employee_id="emp-002",
        document_type_code="CONTRATO",
        issue_on="2025-01-01",
        expires_on="2025-02-03",
        status="vigente",
        metadata={"issuer": "rrhh"},
    )

    result = alarm_event_service.evaluate_documents(documents=[doc1, doc2], evaluation_date="2025-01-24")
    assert result.events == []
    assert result.run.scanned_documents == 2
    assert result.run.expired_documents == 1
    assert result.run.matched_documents == 0
