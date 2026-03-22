from app.modules.cash_sessions.service import cash_session_service


def setup_function() -> None:
    cash_session_service.reset_state()


def test_cash_session_service_create_get_update_delete() -> None:
    created = cash_session_service.create_session(
        branch_id="br-001",
        opened_by="usr-001",
        opening_amount=100000,
        status="open",
    )

    fetched = cash_session_service.get_session(created.id)
    assert fetched.branch_id == "br-001"

    updated = cash_session_service.update_session(created.id, closing_amount=95000, status="closed")
    assert updated.closing_amount == 95000
    assert updated.status == "closed"

    cash_session_service.delete_session(created.id)

    try:
        cash_session_service.get_session(created.id)
        assert False, "expected KeyError"
    except KeyError as exc:
        assert str(exc) == "'cash session not found'"


def test_cash_session_service_prevents_duplicate_open_session_per_operator_branch() -> None:
    cash_session_service.create_session(
        branch_id="br-001",
        opened_by="usr-001",
        opening_amount=100000,
        status="open",
    )

    try:
        cash_session_service.create_session(
            branch_id="br-001",
            opened_by="usr-001",
            opening_amount=50000,
            status="open",
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "operator already has an open cash session in this branch"


def test_cash_session_service_rejects_updates_after_closed() -> None:
    created = cash_session_service.create_session(
        branch_id="br-001",
        opened_by="usr-001",
        opening_amount=100000,
        status="open",
    )
    closed = cash_session_service.update_session(created.id, closing_amount=98000, status="closed")
    assert closed.status == "closed"

    try:
        cash_session_service.update_session(created.id, closing_amount=99000, status=None)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "only open cash sessions can be updated"
