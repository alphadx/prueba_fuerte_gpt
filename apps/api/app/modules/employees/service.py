"""In-memory service layer for employees module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass
class Employee:
    id: str
    employee_code: str
    full_name: str
    role: str
    is_active: bool


class EmployeeService:
    def __init__(self) -> None:
        self._by_id: dict[str, Employee] = {}
        self._ids_by_code: dict[str, str] = {}
        self._seq = 0
        self._lock = RLock()

    def list_employees(self) -> list[Employee]:
        with self._lock:
            return [Employee(**vars(item)) for item in self._by_id.values()]

    def create_employee(self, *, employee_code: str, full_name: str, role: str, is_active: bool) -> Employee:
        with self._lock:
            if employee_code in self._ids_by_code:
                raise ValueError("employee code already exists")
            self._seq += 1
            employee_id = f"emp-{self._seq:04d}"
            employee = Employee(
                id=employee_id,
                employee_code=employee_code,
                full_name=full_name,
                role=role,
                is_active=is_active,
            )
            self._by_id[employee_id] = employee
            self._ids_by_code[employee_code] = employee_id
            return Employee(**vars(employee))

    def get_employee(self, employee_id: str) -> Employee:
        with self._lock:
            if employee_id not in self._by_id:
                raise KeyError("employee not found")
            return Employee(**vars(self._by_id[employee_id]))

    def update_employee(self, employee_id: str, *, full_name: str | None, role: str | None, is_active: bool | None) -> Employee:
        with self._lock:
            if employee_id not in self._by_id:
                raise KeyError("employee not found")
            employee = self._by_id[employee_id]
            if full_name is not None:
                employee.full_name = full_name
            if role is not None:
                employee.role = role
            if is_active is not None:
                employee.is_active = is_active
            return Employee(**vars(employee))

    def delete_employee(self, employee_id: str) -> None:
        with self._lock:
            employee = self.get_employee(employee_id)
            del self._by_id[employee_id]
            del self._ids_by_code[employee.employee_code]

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_code.clear()
            self._seq = 0


employee_service = EmployeeService()
