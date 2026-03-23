from app.modules.alerts.notifications import alert_notification_service
from app.modules.alerts.service import AlarmEvent


def setup_function() -> None:
    alert_notification_service.reset_state()


def test_notification_service_dispatches_in_app_and_email() -> None:
    event = AlarmEvent(
        id="alarm-0001",
        employee_document_id="edoc-0001",
        employee_id="emp-001",
        document_type_code="LIC",
        threshold_days=7,
        days_to_expire=7,
        evaluation_date="2025-01-24",
        dedupe_key="edoc-0001:7:2025-01-24",
        status="pending",
        source="daily_evaluator",
        generated_at="2025-01-24T00:00:00Z",
        rule_snapshot={"threshold_days": 7, "evaluation_date": "2025-01-24"},
        notification_statuses={},
    )

    attempts = alert_notification_service.dispatch_event(event=event)
    assert len(attempts) == 2
    assert {item.channel for item in attempts} == {"in_app", "email"}
    assert all(item.status == "sent" for item in attempts)
