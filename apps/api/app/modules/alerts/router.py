"""Alerts API router for HR document expiry evaluation."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.alerts.notifications import NotificationAttempt, alert_notification_service
from app.modules.alerts.schemas import (
    AlarmEventListResponse,
    AlarmEventResponse,
    AlertEvaluationRunListResponse,
    AlertEvaluationRunResponse,
    DispatchPendingNotificationsResponse,
    EvaluateAlertsRequest,
    EvaluateAlertsResponse,
    NotificationAttemptListResponse,
    NotificationAttemptResponse,
)
from app.modules.alerts.service import AlarmEvent, AlertEvaluationRun, alarm_event_service
from app.modules.employee_documents.service import employee_document_service
from app.services.queue import queue_client

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _to_response(item: AlarmEvent) -> AlarmEventResponse:
    return AlarmEventResponse(
        id=item.id,
        employee_document_id=item.employee_document_id,
        employee_id=item.employee_id,
        document_type_code=item.document_type_code,
        threshold_days=item.threshold_days,
        days_to_expire=item.days_to_expire,
        evaluation_date=item.evaluation_date,
        dedupe_key=item.dedupe_key,
        status=item.status,
        source=item.source,
        generated_at=item.generated_at,
        rule_snapshot=item.rule_snapshot,
        notification_statuses=item.notification_statuses,
    )


def _to_run_response(item: AlertEvaluationRun) -> AlertEvaluationRunResponse:
    return AlertEvaluationRunResponse(
        id=item.id,
        evaluation_date=item.evaluation_date,
        thresholds=list(item.thresholds),
        scanned_documents=item.scanned_documents,
        matched_documents=item.matched_documents,
        duplicate_events=item.duplicate_events,
        expired_documents=item.expired_documents,
        generated_events=item.generated_events,
        created_at=item.created_at,
    )


def _to_attempt_response(item: NotificationAttempt) -> NotificationAttemptResponse:
    return NotificationAttemptResponse(
        id=item.id,
        event_id=item.event_id,
        channel=item.channel,
        status=item.status,
        detail=item.detail,
        attempted_at=item.attempted_at,
    )


@router.post("/evaluate", response_model=EvaluateAlertsResponse)
def evaluate_alerts(
    payload: EvaluateAlertsRequest,
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> EvaluateAlertsResponse:
    documents = employee_document_service.list_documents()
    result = alarm_event_service.evaluate_documents(documents=documents, evaluation_date=payload.evaluation_date)

    queued = 0
    for event in result.events:
        queue_client.enqueue_alert(
            {
                "event_id": event.id,
                "employee_id": event.employee_id,
                "document_type_code": event.document_type_code,
                "threshold_days": event.threshold_days,
                "days_to_expire": event.days_to_expire,
                "evaluation_date": event.evaluation_date,
                "dedupe_key": event.dedupe_key,
            }
        )
        queued += 1

    record_audit_event(
        actor_id=auth.subject,
        action="alerts.evaluate",
        entity=payload.evaluation_date,
        metadata={
            "run_id": result.run.id,
            "generated": len(result.events),
            "queued": queued,
            "duplicates": result.run.duplicate_events,
        },
    )

    return EvaluateAlertsResponse(
        generated=len(result.events),
        queued=queued,
        run=_to_run_response(result.run),
        items=[_to_response(item) for item in result.events],
    )


@router.post("/dispatch-pending", response_model=DispatchPendingNotificationsResponse)
def dispatch_pending_notifications(
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> DispatchPendingNotificationsResponse:
    pending_events = alarm_event_service.list_pending_events()

    sent_attempts = 0
    failed_attempts = 0
    processed_events = 0

    for event in pending_events:
        attempts = alert_notification_service.dispatch_event(event=event)
        processed_events += 1
        for attempt in attempts:
            alarm_event_service.update_notification_status(
                event_id=event.id,
                channel=attempt.channel,
                status=attempt.status,
            )
            if attempt.status == "sent":
                sent_attempts += 1
            else:
                failed_attempts += 1

    record_audit_event(
        actor_id=auth.subject,
        action="alerts.dispatch_pending",
        entity="notifications",
        metadata={
            "processed_events": processed_events,
            "sent_attempts": sent_attempts,
            "failed_attempts": failed_attempts,
        },
    )

    return DispatchPendingNotificationsResponse(
        processed_events=processed_events,
        sent_attempts=sent_attempts,
        failed_attempts=failed_attempts,
    )


@router.get("/events", response_model=AlarmEventListResponse)
def list_alarm_events(_: AuthContext = Depends(require_roles("admin", "rrhh"))) -> AlarmEventListResponse:
    return AlarmEventListResponse(items=[_to_response(item) for item in alarm_event_service.list_events()])


@router.get("/evaluations", response_model=AlertEvaluationRunListResponse)
def list_evaluation_runs(_: AuthContext = Depends(require_roles("admin", "rrhh"))) -> AlertEvaluationRunListResponse:
    return AlertEvaluationRunListResponse(items=[_to_run_response(item) for item in alarm_event_service.list_runs()])


@router.get("/notifications", response_model=NotificationAttemptListResponse)
def list_notification_attempts(_: AuthContext = Depends(require_roles("admin", "rrhh"))) -> NotificationAttemptListResponse:
    attempts = alert_notification_service.list_attempts()
    return NotificationAttemptListResponse(items=[_to_attempt_response(item) for item in attempts])
