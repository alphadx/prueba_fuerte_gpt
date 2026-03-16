"""API router for stage 5 pickup checkout backend and state machine."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.orders.schemas import (
    CatalogProductListResponse,
    CatalogProductResponse,
    OrderTransitionRequest,
    OrderTransitionResponse,
    PickupCheckoutConfirmRequest,
    PickupCheckoutConfirmResponse,
    PickupOrderResponse,
    PickupSlotListResponse,
)
from app.modules.orders.service import catalog_service, pickup_order_service, pickup_slot_service

router = APIRouter(tags=["orders", "checkout", "catalog", "pickup_slots"])


@router.get("/catalog/products", response_model=CatalogProductListResponse)
def list_catalog_products(
    branch_id: str = Query(min_length=1),
    _: AuthContext = Depends(require_roles("admin", "cajero")),
) -> CatalogProductListResponse:
    try:
        items = [CatalogProductResponse(**item) for item in catalog_service.list_products_by_branch(branch_id)]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="INVALID_BRANCH") from exc

    return CatalogProductListResponse(items=items)


@router.get("/pickup-slots", response_model=PickupSlotListResponse)
def list_pickup_slots(
    branch_id: str = Query(min_length=1),
    date: str = Query(min_length=1),
    _: AuthContext = Depends(require_roles("admin", "cajero")),
) -> PickupSlotListResponse:
    try:
        data = pickup_slot_service.list_slots(branch_id=branch_id, date=date)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="NO_SLOTS_CONFIGURED") from exc
    return PickupSlotListResponse(**data)


@router.post("/checkout/pickup/confirm", response_model=PickupCheckoutConfirmResponse, status_code=status.HTTP_201_CREATED)
def confirm_pickup_checkout(
    payload: PickupCheckoutConfirmRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=3),
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> PickupCheckoutConfirmResponse:
    try:
        created = pickup_order_service.create_order(
            branch_id=payload.branch_id,
            pickup_slot_id=payload.pickup_slot_id,
            customer=payload.customer.model_dump(),
            lines_payload=[line.model_dump() for line in payload.lines],
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        detail = "INSUFFICIENT_STOCK_AT_CONFIRMATION" if "stock" in str(exc) else str(exc)
        record_audit_event(
            actor_id=auth.subject,
            action="orders.checkout.rejected",
            entity=payload.branch_id,
            metadata={"reason": detail, "idempotency_key": idempotency_key},
        )
        raise HTTPException(status_code=409, detail=detail) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND") from exc

    record_audit_event(
        actor_id=auth.subject,
        action="orders.checkout.confirm",
        entity=created.order_id,
        metadata={"state": created.state, "branch_id": created.branch_id},
    )
    return PickupCheckoutConfirmResponse(
        order_id=created.order_id,
        order_state=created.state,
        branch_id=created.branch_id,
        pickup_slot_id=created.pickup_slot_id,
        idempotency_key=created.idempotency_key,
        totals={"subtotal": created.subtotal, "currency": "CLP"},
        lines=[
            {
                "product_id": line.product_id,
                "qty": line.qty,
                "unit_price": line.unit_price,
                "line_total": line.line_total,
            }
            for line in created.lines
        ],
    )


@router.get("/orders/{order_id}", response_model=PickupOrderResponse)
def get_pickup_order(
    order_id: str,
    _: AuthContext = Depends(require_roles("admin", "cajero")),
) -> PickupOrderResponse:
    try:
        order = pickup_order_service.get_order(order_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND") from exc

    return PickupOrderResponse(
        order_id=order.order_id,
        state=order.state,
        branch_id=order.branch_id,
        pickup_slot_id=order.pickup_slot_id,
        customer=order.customer,
        idempotency_key=order.idempotency_key,
        subtotal=order.subtotal,
        lines=[
            {
                "product_id": line.product_id,
                "qty": line.qty,
                "unit_price": line.unit_price,
                "line_total": line.line_total,
            }
            for line in order.lines
        ],
        transitions=[
            {
                "previous_state": event.previous_state,
                "current_state": event.current_state,
                "actor": event.actor,
                "reason": event.reason,
            }
            for event in order.transitions
        ],
    )


@router.post("/orders/{order_id}/transitions", response_model=OrderTransitionResponse)
def transition_pickup_order(
    order_id: str,
    payload: OrderTransitionRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> OrderTransitionResponse:
    try:
        current_order = pickup_order_service.get_order(order_id)
        updated = pickup_order_service.transition_order(
            order_id=order_id,
            target_state=payload.target_state,
            actor=auth.subject,
            reason=payload.reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND") from exc
    except ValueError as exc:
        detail = str(exc)
        if "invalid" in detail:
            detail = "INVALID_ORDER_TRANSITION"
        elif "already" in detail:
            detail = "ORDER_ALREADY_IN_TARGET_STATE"

        record_audit_event(
            actor_id=auth.subject,
            action="orders.transition.rejected",
            entity=order_id,
            metadata={"target_state": payload.target_state, "reason": detail},
        )
        raise HTTPException(status_code=409, detail=detail) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="orders.transition",
        entity=order_id,
        metadata={
            "previous_state": current_order.state,
            "current_state": updated.state,
            "reason": payload.reason,
        },
    )
    return OrderTransitionResponse(
        order_id=updated.order_id,
        previous_state=current_order.state,
        current_state=updated.state,
    )
