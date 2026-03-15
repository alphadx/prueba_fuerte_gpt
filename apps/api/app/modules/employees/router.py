"""Employees API router with RBAC and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.employees.schemas import (
    EmployeeCreateRequest,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdateRequest,
)
from app.modules.employees.service import Employee, employee_service

router = APIRouter(prefix="/employees", tags=["employees"])


def _to_response(employee: Employee) -> EmployeeResponse:
    return EmployeeResponse(
        id=employee.id,
        employee_code=employee.employee_code,
        full_name=employee.full_name,
        role=employee.role,
        is_active=employee.is_active,
    )


@router.get("", response_model=EmployeeListResponse)
def list_employees(_: AuthContext = Depends(require_roles("admin", "rrhh"))) -> EmployeeListResponse:
    return EmployeeListResponse(items=[_to_response(item) for item in employee_service.list_employees()])


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreateRequest, auth: AuthContext = Depends(require_roles("admin", "rrhh"))) -> EmployeeResponse:
    try:
        created = employee_service.create_employee(
            employee_code=payload.employee_code,
            full_name=payload.full_name,
            role=payload.role,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="employees.create", entity=created.id, metadata={"role": created.role})
    return _to_response(created)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: str, _: AuthContext = Depends(require_roles("admin", "rrhh"))) -> EmployeeResponse:
    try:
        return _to_response(employee_service.get_employee(employee_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdateRequest,
    auth: AuthContext = Depends(require_roles("admin", "rrhh")),
) -> EmployeeResponse:
    try:
        updated = employee_service.update_employee(
            employee_id,
            full_name=payload.full_name,
            role=payload.role,
            is_active=payload.is_active,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="employees.update", entity=updated.id, metadata={"role": updated.role})
    return _to_response(updated)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_employee(employee_id: str, auth: AuthContext = Depends(require_roles("admin"))) -> Response:
    try:
        employee_service.delete_employee(employee_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(actor_id=auth.subject, action="employees.delete", entity=employee_id, metadata={})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
