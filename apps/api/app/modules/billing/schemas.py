"""Schemas for billing tax document tracking."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BillingProcessRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=200)


class BillingDocumentResponse(BaseModel):
    sale_id: str
    idempotency_key: str
    document_type: str
    status: str
    attempts: int
    max_attempts: int
    provider_document_id: str | None = None
    track_id: str | None = None
    folio: str | None = None
    xml_url: str | None = None
    pdf_url: str | None = None
    raw_payload_ref: str | None = None
    sii_status: str | None = None
    last_error: str | None = None


class BillingWorkerProcessResponse(BaseModel):
    enqueued: int
    processed: int
    succeeded: int
    failed: int
