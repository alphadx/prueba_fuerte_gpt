from app.modules.document_types.service import document_type_service


def setup_function() -> None:
    document_type_service.reset_state()


def test_document_type_service_create_get_update_delete() -> None:
    created = document_type_service.create_document_type(
        code="LIC",
        name="Licencia Conducir",
        requires_expiry=True,
        is_active=True,
    )

    fetched = document_type_service.get_document_type(created.id)
    assert fetched.code == "LIC"

    updated = document_type_service.update_document_type(
        created.id,
        name="Licencia Clase B",
        requires_expiry=False,
        is_active=False,
    )
    assert updated.name == "Licencia Clase B"
    assert updated.requires_expiry is False
    assert updated.is_active is False

    document_type_service.delete_document_type(created.id)

    try:
        document_type_service.get_document_type(created.id)
        assert False, "expected KeyError"
    except KeyError as exc:
        assert str(exc) == "'document type not found'"


def test_document_type_service_reject_duplicate_code() -> None:
    document_type_service.create_document_type(
        code="LIC",
        name="Licencia Conducir",
        requires_expiry=True,
        is_active=True,
    )

    try:
        document_type_service.create_document_type(
            code="LIC",
            name="Otra Licencia",
            requires_expiry=False,
            is_active=True,
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "document type code already exists"
