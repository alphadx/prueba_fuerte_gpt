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
    PaymentMethodFlagListResponse,
    PaymentMethodFlagResponse,
    PaymentMethodFlagUpsertRequest,
    PaymentResponse,
    PaymentUpdateRequest,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
    StubPaymentCreateRequest,
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






@router.get("/flags", response_model=PaymentMethodFlagListResponse)
def list_payment_flags(auth: AuthContext = Depends(require_roles("admin", "cajero"))) -> PaymentMethodFlagListResponse:
    flags = payment_service.list_method_flags()
    record_audit_event(actor_id=auth.subject, action="payments.flags.list", entity="payments", metadata={"count": len(flags)})
    return PaymentMethodFlagListResponse(
        items=[
            PaymentMethodFlagResponse(
                branch_id=item.branch_id,
                channel=item.channel,
                method=item.method,
                enabled=item.enabled,
            )
            for item in flags
        ]
    )


@router.put("/flags", response_model=PaymentMethodFlagResponse)
def upsert_payment_flag(
    payload: PaymentMethodFlagUpsertRequest,
    auth: AuthContext = Depends(require_roles("admin")),
) -> PaymentMethodFlagResponse:
    flag = payment_service.set_method_flag(
        branch_id=payload.branch_id,
        channel=payload.channel,
        method=payload.method,
        enabled=payload.enabled,
    )
    record_audit_event(
        actor_id=auth.subject,
        action="payments.flags.upsert",
        entity=f"{flag.branch_id}:{flag.channel}:{flag.method}",
        metadata={"enabled": flag.enabled},
    )
    return PaymentMethodFlagResponse(
        branch_id=flag.branch_id,
        channel=flag.channel,
        method=flag.method,
        enabled=flag.enabled,
    )


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
        message = str(exc)
        if message == "payment method disabled for branch/channel":
            raise HTTPException(status_code=403, detail=message) from exc
        raise HTTPException(status_code=409, detail=message) from exc

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



@router.post("/stubs/{provider}", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_stub_payment(
    provider: str,
    payload: StubPaymentCreateRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> PaymentResponse:
    try:
        created = payment_service.create_stub_payment(
            provider=provider,
            sale_id=payload.sale_id,
            amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            channel=payload.channel,
            currency=payload.currency,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        message = str(exc)
        if message == "unsupported provider":
            raise HTTPException(status_code=400, detail=message) from exc
        if message == "payment method disabled for branch/channel":
            raise HTTPException(status_code=403, detail=message) from exc
        raise HTTPException(status_code=409, detail=message) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="payments.stub.create",
        entity=created.id,
        metadata={"provider": provider, "sale_id": created.sale_id, "amount": created.amount},
    )
    return _to_response(created)




@router.post("/webhooks/{provider}", response_model=PaymentWebhookResponse)
def process_payment_webhook(
    provider: str,
    payload: PaymentWebhookRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> PaymentWebhookResponse:
    try:
        result = payment_service.process_webhook_event(
            provider=provider,
            payload=payload.payload,
            signature=payload.signature,
        )
    except ValueError as exc:
        message = str(exc)
        if message == "unsupported provider":
            raise HTTPException(status_code=400, detail=message) from exc
        if message == "invalid signature":
            raise HTTPException(status_code=401, detail=message) from exc
        raise HTTPException(status_code=409, detail=message) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="payments.webhook.process",
        entity=result.event_id,
        metadata={
            "provider": result.provider,
            "duplicated": result.duplicated,
            "payment_id": result.payment_id,
            "current_status": result.current_status,
        },
    )
    return PaymentWebhookResponse(
        provider=result.provider,
        event_id=result.event_id,
        duplicated=result.duplicated,
        payment_id=result.payment_id,
        previous_status=result.previous_status,
        current_status=result.current_status,
    )


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
