"""Payments API router with RBAC and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.payments.schemas import (
    CashPaymentCreateRequest,
    CashReconciliationResponse,
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentResponse,
    PaymentUpdateRequest,
)
from app.modules.payments.service import Payment, payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


def _to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        sale_id=payment.sale_id,
        amount=payment.amount,
        method=payment.method,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
    )


@router.get("", response_model=PaymentListResponse)
def list_payments(_: AuthContext = Depends(require_roles("admin", "cajero"))) -> PaymentListResponse:
    return PaymentListResponse(items=[_to_response(item) for item in payment_service.list_payments()])




@router.post("/cash", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_cash_payment(
    payload: CashPaymentCreateRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> PaymentResponse:
    try:
        created = payment_service.create_cash_payment(
            sale_id=payload.sale_id,
            amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            channel=payload.channel,
            currency=payload.currency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="payments.cash.create",
        entity=created.id,
        metadata={"sale_id": created.sale_id, "branch_id": payload.branch_id, "amount": created.amount},
    )
    return _to_response(created)


@router.get("/cash/reconciliation/{branch_id}", response_model=CashReconciliationResponse)
def reconcile_cash_branch(
    branch_id: str,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> CashReconciliationResponse:
    report = payment_service.reconcile_cash_by_branch(branch_id=branch_id)
    record_audit_event(
        actor_id=auth.subject,
        action="payments.cash.reconciliation",
        entity=branch_id,
        metadata=report,
    )
    return CashReconciliationResponse(**report)

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreateRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> PaymentResponse:
    try:
        created = payment_service.create_payment(
            sale_id=payload.sale_id,
            amount=payload.amount,
            method=payload.method,
            status=payload.status,
            idempotency_key=payload.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="payments.create",
        entity=created.id,
        metadata={"sale_id": created.sale_id, "amount": created.amount, "status": created.status},
    )
    return _to_response(created)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str, _: AuthContext = Depends(require_roles("admin", "cajero"))) -> PaymentResponse:
    try:
        return _to_response(payment_service.get_payment(payment_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: str,
    payload: PaymentUpdateRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> PaymentResponse:
    try:
        updated = payment_service.update_payment(payment_id, status=payload.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="payments.update",
        entity=updated.id,
        metadata={"status": updated.status},
    )
    return _to_response(updated)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_payment(payment_id: str, auth: AuthContext = Depends(require_roles("admin"))) -> Response:
    try:
        payment_service.delete_payment(payment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="payments.delete", entity=payment_id, metadata={})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
