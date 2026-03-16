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
