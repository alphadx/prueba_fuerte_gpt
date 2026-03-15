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
