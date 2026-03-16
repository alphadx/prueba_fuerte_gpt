from app.modules.employee_documents.service import employee_document_service


def setup_function() -> None:
    employee_document_service.reset_state()


def test_employee_document_service_create_get_update_delete() -> None:
    created = employee_document_service.create_document(
        employee_id="emp-001",
        document_type_code="LIC",
        issue_on="2025-01-01",
        expires_on="2027-12-31",
        status="vigente",
        metadata={"issuer": "municipalidad"},
    )

    fetched = employee_document_service.get_document(created.id)
    assert fetched.employee_id == "emp-001"
    assert fetched.issue_on == "2025-01-01"
    assert fetched.metadata["issuer"] == "municipalidad"

    updated = employee_document_service.update_document(
        created.id,
        issue_on=None,
        expires_on=None,
        status="por_vencer",
        metadata={"issuer": "seremi"},
    )
    assert updated.status == "por_vencer"
    assert updated.metadata["issuer"] == "seremi"

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
        issue_on="2025-01-01",
        expires_on="2027-12-31",
        status="vigente",
        metadata={"issuer": "municipalidad"},
    )

    try:
        employee_document_service.create_document(
            employee_id="emp-001",
            document_type_code="LIC",
            issue_on="2025-01-01",
            expires_on="2028-01-01",
            status="vigente",
            metadata={"issuer": "municipalidad"},
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "employee document already exists"
