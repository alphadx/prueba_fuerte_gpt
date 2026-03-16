"""Billing endpoints for sandbox tax document lifecycle."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.billing.schemas import BillingDocumentResponse, BillingProcessRequest, BillingWorkerProcessResponse
from app.modules.billing.service import BillingDocument, billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


def _to_response(doc: BillingDocument) -> BillingDocumentResponse:
    return BillingDocumentResponse(
        sale_id=doc.sale_id,
        idempotency_key=doc.idempotency_key,
        document_type=doc.document_type,
        status=doc.status,
        attempts=doc.attempts,
        max_attempts=doc.max_attempts,
        provider_document_id=doc.provider_document_id,
        track_id=doc.track_id,
        folio=doc.folio,
        xml_url=doc.xml_url,
        pdf_url=doc.pdf_url,
        raw_payload_ref=doc.raw_payload_ref,
        sii_status=doc.sii_status,
        last_error=doc.last_error,
        retry_after_batches=doc.retry_after_batches,
        dead_lettered=doc.dead_lettered,
    )


@router.get("/documents/{sale_id}", response_model=BillingDocumentResponse)
def get_billing_document(
    sale_id: str,
    document_type: str = Query(default="boleta", min_length=1),
    _: AuthContext = Depends(require_roles("admin", "cajero")),
) -> BillingDocumentResponse:
    try:
        return _to_response(billing_service.get_by_sale_id(sale_id, document_type=document_type))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/worker/process", response_model=BillingWorkerProcessResponse)
def process_billing_queue(
    payload: BillingProcessRequest,
    _: AuthContext = Depends(require_roles("admin")),
) -> BillingWorkerProcessResponse:
    enqueued, processed, succeeded, failed, dead_lettered = billing_service.process_worker_batch(limit=payload.limit)
    return BillingWorkerProcessResponse(
        enqueued=enqueued, processed=processed, succeeded=succeeded, failed=failed, dead_lettered=dead_lettered
    )


@router.post("/documents/{sale_id}/refresh-status", response_model=BillingDocumentResponse)
def refresh_billing_document_status(
    sale_id: str,
    document_type: str = Query(default="boleta", min_length=1),
    _: AuthContext = Depends(require_roles("admin", "cajero")),
) -> BillingDocumentResponse:
    try:
        return _to_response(billing_service.refresh_status(sale_id=sale_id, document_type=document_type))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
