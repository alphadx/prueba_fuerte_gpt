"""Sales API router for POS flow."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.sales.schemas import SaleCompleteRequest, SaleListResponse, SaleResponse
from app.modules.sales.service import Sale, sale_service

router = APIRouter(prefix="/sales", tags=["sales"])


def _to_response(sale: Sale) -> SaleResponse:
    return SaleResponse(
        id=sale.id,
        branch_id=sale.branch_id,
        cash_session_id=sale.cash_session_id,
        sold_by=sale.sold_by,
        status=sale.status,
        subtotal=sale.subtotal,
        taxes=sale.taxes,
        total=sale.total,
        payment_method=sale.payment_method,
        payment_status=sale.payment_status,
        billing_event_emitted=sale.billing_event_emitted,
        lines=[
            {
                "product_id": line.product_id,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "line_subtotal": line.line_subtotal,
                "line_tax": line.line_tax,
                "line_total": line.line_total,
            }
            for line in sale.lines
        ],
    )


@router.get("", response_model=SaleListResponse)
def list_sales(_: AuthContext = Depends(require_roles("admin", "cajero"))) -> SaleListResponse:
    return SaleListResponse(items=[_to_response(item) for item in sale_service.list_sales()])


@router.post("/complete", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def complete_sale(
    payload: SaleCompleteRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> SaleResponse:
    try:
        created = sale_service.complete_sale(
            branch_id=payload.branch_id,
            cash_session_id=payload.cash_session_id,
            sold_by=payload.sold_by,
            payment_method=payload.payment_method,
            lines_payload=[line.model_dump() for line in payload.lines],
        )
    except (ValueError, KeyError) as exc:
        record_audit_event(
            actor_id=auth.subject,
            action="sales.complete.rejected",
            entity=payload.cash_session_id,
            metadata={"reason": str(exc), "branch_id": payload.branch_id, "payment_method": payload.payment_method},
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="sales.complete",
        entity=created.id,
        metadata={"status": created.status, "total": created.total, "payment_method": created.payment_method},
    )
    return _to_response(created)
