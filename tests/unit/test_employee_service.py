from app.modules.employees.service import employee_service


def setup_function() -> None:
    employee_service.reset_state()


def test_employee_service_create_get_update_delete() -> None:
    created = employee_service.create_employee(
        employee_code="E-001",
        full_name="Ana Pérez",
        role="bodega",
        is_active=True,
    )

    fetched = employee_service.get_employee(created.id)
    assert fetched.employee_code == "E-001"

    updated = employee_service.update_employee(created.id, full_name="Ana P.", role="cajero", is_active=False)
    assert updated.full_name == "Ana P."
    assert updated.role == "cajero"
    assert updated.is_active is False

    employee_service.delete_employee(created.id)

    try:
        employee_service.get_employee(created.id)
        assert False, "expected KeyError"
    except KeyError as exc:
        assert str(exc) == "'employee not found'"


def test_employee_service_reject_duplicate_code() -> None:
    employee_service.create_employee(
        employee_code="E-001",
        full_name="Ana Pérez",
        role="bodega",
        is_active=True,
    )

    try:
        employee_service.create_employee(
            employee_code="E-001",
            full_name="Juan Pérez",
            role="rrhh",
            is_active=True,
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "employee code already exists"
