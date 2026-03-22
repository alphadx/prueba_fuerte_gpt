"""Schemas for alerts evaluation and listing."""

from pydantic import BaseModel, Field


class EvaluateAlertsRequest(BaseModel):
    evaluation_date: str = Field(min_length=1)


class AlarmEventResponse(BaseModel):
    id: str
    employee_document_id: str
    employee_id: str
    document_type_code: str
    threshold_days: int
    days_to_expire: int
    evaluation_date: str
    dedupe_key: str
    status: str
    source: str
    generated_at: str
    rule_snapshot: dict[str, object]
    notification_statuses: dict[str, str]


class NotificationAttemptResponse(BaseModel):
    id: str
    event_id: str
    channel: str
    status: str
    detail: str
    attempted_at: str


class NotificationAttemptListResponse(BaseModel):
    items: list[NotificationAttemptResponse]


class DispatchPendingNotificationsResponse(BaseModel):
    processed_events: int
    sent_attempts: int
    failed_attempts: int


class AlertEvaluationRunResponse(BaseModel):
    id: str
    evaluation_date: str
    thresholds: list[int]
    scanned_documents: int
    matched_documents: int
    duplicate_events: int
    expired_documents: int
    generated_events: int
    created_at: str


class EvaluateAlertsResponse(BaseModel):
    generated: int
    queued: int
    run: AlertEvaluationRunResponse
    items: list[AlarmEventResponse]


class AlarmEventListResponse(BaseModel):
    items: list[AlarmEventResponse]


class AlertEvaluationRunListResponse(BaseModel):
    items: list[AlertEvaluationRunResponse]


class AlertsSummaryResponse(BaseModel):
    total_events: int
    pending_events: int
    sent_events: int
    partially_failed_events: int
    failed_events: int
    total_notification_attempts: int
    sent_notification_attempts: int
    failed_notification_attempts: int
    total_evaluations: int
