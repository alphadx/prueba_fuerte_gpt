from app.modules.users.service import user_service


def setup_function() -> None:
    user_service.reset_state()


def test_user_service_create_and_get() -> None:
    created = user_service.create_user(username="admin", full_name="Administrador", role="admin", is_active=True)

    fetched = user_service.get_user(created.id)

    assert fetched.username == "admin"
    assert fetched.role == "admin"


def test_user_service_rejects_duplicate_username() -> None:
    user_service.create_user(username="admin", full_name="Administrador", role="admin", is_active=True)

    try:
        user_service.create_user(username="admin", full_name="Otro", role="cajero", is_active=True)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "username already exists"


def test_user_service_update_and_delete() -> None:
    created = user_service.create_user(username="jdoe", full_name="John Doe", role="cajero", is_active=True)

    updated = user_service.update_user(created.id, full_name="John D.", role="bodega", is_active=False)
    assert updated.full_name == "John D."
    assert updated.role == "bodega"
    assert updated.is_active is False

    user_service.delete_user(created.id)

    try:
        user_service.get_user(created.id)
        assert False, "expected KeyError"
    except KeyError as exc:
        assert str(exc) == "'user not found'"
