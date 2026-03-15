from app.modules.employee_documents.service import employee_document_service


def setup_function() -> None:
    employee_document_service.reset_state()


def test_employee_document_service_create_get_update_delete() -> None:
    created = employee_document_service.create_document(
        employee_id="emp-001",
        document_type_code="LIC",
        expires_on="2027-12-31",
        status="vigente",
    )

    fetched = employee_document_service.get_document(created.id)
    assert fetched.employee_id == "emp-001"

    updated = employee_document_service.update_document(created.id, expires_on=None, status="por_vencer")
    assert updated.status == "por_vencer"

    employee_document_service.delete_document(created.id)

    try:
        employee_document_service.get_document(created.id)
        assert False, "expected KeyError"
    except KeyError as exc:
        assert str(exc) == "'employee document not found'"


def test_employee_document_service_reject_duplicate_key() -> None:
    employee_document_service.create_document(
        employee_id="emp-001",
        document_type_code="LIC",
        expires_on="2027-12-31",
        status="vigente",
    )

    try:
        employee_document_service.create_document(
            employee_id="emp-001",
            document_type_code="LIC",
            expires_on="2028-01-01",
            status="vigente",
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "employee document already exists"
