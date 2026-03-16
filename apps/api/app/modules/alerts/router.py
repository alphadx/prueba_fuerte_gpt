"""Alerts API router for HR document expiry evaluation."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.alerts.schemas import (
    AlarmEventListResponse,
    AlarmEventResponse,
    EvaluateAlertsRequest,
    EvaluateAlertsResponse,
)
from app.modules.alerts.service import AlarmEvent, alarm_event_service
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
        status=item.status,
    )


@router.post("/evaluate", response_model=EvaluateAlertsResponse)
def evaluate_alerts(
    payload: EvaluateAlertsRequest,
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> EvaluateAlertsResponse:
    documents = employee_document_service.list_documents()
    created = alarm_event_service.evaluate_documents(documents=documents, evaluation_date=payload.evaluation_date)

    queued = 0
    for event in created:
        queue_client.enqueue_alert(
            {
                "event_id": event.id,
                "employee_id": event.employee_id,
                "document_type_code": event.document_type_code,
                "threshold_days": event.threshold_days,
                "days_to_expire": event.days_to_expire,
                "evaluation_date": event.evaluation_date,
            }
        )
        queued += 1

    record_audit_event(
        actor_id=auth.subject,
        action="alerts.evaluate",
        entity=payload.evaluation_date,
        metadata={"generated": len(created), "queued": queued},
    )

    return EvaluateAlertsResponse(generated=len(created), queued=queued, items=[_to_response(item) for item in created])


@router.get("/events", response_model=AlarmEventListResponse)
def list_alarm_events(_: AuthContext = Depends(require_roles("admin", "rrhh"))) -> AlarmEventListResponse:
    return AlarmEventListResponse(items=[_to_response(item) for item in alarm_event_service.list_events()])
