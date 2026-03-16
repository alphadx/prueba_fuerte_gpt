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
    status: str


class EvaluateAlertsResponse(BaseModel):
    generated: int
    queued: int
    items: list[AlarmEventResponse]


class AlarmEventListResponse(BaseModel):
    items: list[AlarmEventResponse]
