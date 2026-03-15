from app.modules.branches.service import branch_service


def setup_function() -> None:
    branch_service.reset_state()


def test_branch_service_create_get_update_delete() -> None:
    created = branch_service.create_branch(code="CASA", name="Casa Matriz", address="Av. Central 123", is_active=True)

    fetched = branch_service.get_branch(created.id)
    assert fetched.code == "CASA"

    updated = branch_service.update_branch(created.id, name="Casa Norte", address=None, is_active=False)
    assert updated.name == "Casa Norte"
    assert updated.is_active is False

    branch_service.delete_branch(created.id)

    try:
        branch_service.get_branch(created.id)
        assert False, "expected KeyError"
    except KeyError as exc:
        assert str(exc) == "'branch not found'"


def test_branch_service_reject_duplicate_code() -> None:
    branch_service.create_branch(code="CASA", name="Casa Matriz", address="Av. Central 123", is_active=True)

    try:
        branch_service.create_branch(code="CASA", name="Casa 2", address="Otra 456", is_active=True)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "branch code already exists"
