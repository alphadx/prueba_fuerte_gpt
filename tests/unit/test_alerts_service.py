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

    created_first = alarm_event_service.evaluate_documents(
        documents=[doc],
        evaluation_date="2025-01-24",  # 7 days to expire
    )
    assert len(created_first) == 1
    assert created_first[0].threshold_days == 7

    created_second = alarm_event_service.evaluate_documents(
        documents=[doc],
        evaluation_date="2025-01-24",
    )
    assert len(created_second) == 0


def test_alerts_service_ignores_non_threshold_or_expired_documents() -> None:
    doc1 = employee_document_service.create_document(
        employee_id="emp-001",
        document_type_code="LIC",
        issue_on="2025-01-01",
        expires_on="2025-01-20",  # expired for eval date
        status="vigente",
        metadata={"issuer": "municipalidad"},
    )
    doc2 = employee_document_service.create_document(
        employee_id="emp-002",
        document_type_code="CONTRATO",
        issue_on="2025-01-01",
        expires_on="2025-02-03",  # 10 days to expire
        status="vigente",
        metadata={"issuer": "rrhh"},
    )

    created = alarm_event_service.evaluate_documents(
        documents=[doc1, doc2],
        evaluation_date="2025-01-24",
    )
    assert created == []
