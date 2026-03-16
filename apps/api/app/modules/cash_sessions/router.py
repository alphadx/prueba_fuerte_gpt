"""Cash sessions API router with RBAC and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.cash_sessions.schemas import (
    CashSessionCreateRequest,
    CashSessionListResponse,
    CashSessionResponse,
    CashSessionUpdateRequest,
)
from app.modules.cash_sessions.service import CashSession, cash_session_service

router = APIRouter(prefix="/cash-sessions", tags=["cash-sessions"])


def _to_response(session: CashSession) -> CashSessionResponse:
    return CashSessionResponse(
        id=session.id,
        branch_id=session.branch_id,
        opened_by=session.opened_by,
        opening_amount=session.opening_amount,
        closing_amount=session.closing_amount,
        expected_amount=session.expected_amount,
        difference_amount=session.difference_amount,
        status=session.status,
    )


@router.get("", response_model=CashSessionListResponse)
def list_sessions(_: AuthContext = Depends(require_roles("admin", "cajero"))) -> CashSessionListResponse:
    return CashSessionListResponse(items=[_to_response(item) for item in cash_session_service.list_sessions()])


@router.post("", response_model=CashSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: CashSessionCreateRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> CashSessionResponse:
    created = cash_session_service.create_session(
        branch_id=payload.branch_id,
        opened_by=payload.opened_by,
        opening_amount=payload.opening_amount,
        status=payload.status,
    )

    record_audit_event(
        actor_id=auth.subject,
        action="cash_sessions.create",
        entity=created.id,
        metadata={"branch_id": created.branch_id, "opening_amount": created.opening_amount},
    )
    return _to_response(created)


@router.get("/{session_id}", response_model=CashSessionResponse)
def get_session(session_id: str, _: AuthContext = Depends(require_roles("admin", "cajero"))) -> CashSessionResponse:
    try:
        return _to_response(cash_session_service.get_session(session_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{session_id}", response_model=CashSessionResponse)
def update_session(
    session_id: str,
    payload: CashSessionUpdateRequest,
    auth: AuthContext = Depends(require_roles("admin", "cajero")),
) -> CashSessionResponse:
    try:
        updated = cash_session_service.update_session(
            session_id,
            closing_amount=payload.closing_amount,
            status=payload.status,
            cash_delta=payload.cash_delta,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="cash_sessions.update",
        entity=updated.id,
        metadata={"closing_amount": updated.closing_amount, "status": updated.status},
    )
    return _to_response(updated)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_session(session_id: str, auth: AuthContext = Depends(require_roles("admin"))) -> Response:
    try:
        cash_session_service.delete_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="cash_sessions.delete", entity=session_id, metadata={})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
