"""In-memory service layer for cash sessions module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass
class CashSession:
    id: str
    branch_id: str
    opened_by: str
    opening_amount: float
    closing_amount: float | None
    expected_amount: float
    difference_amount: float | None
    status: str


class CashSessionService:
    def __init__(self) -> None:
        self._by_id: dict[str, CashSession] = {}
        self._seq = 0
        self._lock = RLock()

    def list_sessions(self) -> list[CashSession]:
        with self._lock:
            return [CashSession(**vars(item)) for item in self._by_id.values()]

    def create_session(self, *, branch_id: str, opened_by: str, opening_amount: float, status: str) -> CashSession:
        with self._lock:
            if status != "open":
                raise ValueError("cash session must start in open status")
            if any(
                existing.status == "open" and existing.branch_id == branch_id and existing.opened_by == opened_by
                for existing in self._by_id.values()
            ):
                raise ValueError("operator already has an open cash session in this branch")
            self._seq += 1
            session_id = f"cash-{self._seq:04d}"
            session = CashSession(
                id=session_id,
                branch_id=branch_id,
                opened_by=opened_by,
                opening_amount=opening_amount,
                closing_amount=None,
                expected_amount=opening_amount,
                difference_amount=None,
                status=status,
            )
            self._by_id[session_id] = session
            return CashSession(**vars(session))

    def get_session(self, session_id: str) -> CashSession:
        with self._lock:
            if session_id not in self._by_id:
                raise KeyError("cash session not found")
            return CashSession(**vars(self._by_id[session_id]))

    def update_session(self, session_id: str, *, closing_amount: float | None, status: str | None, cash_delta: float | None = None) -> CashSession:
        with self._lock:
            if session_id not in self._by_id:
                raise KeyError("cash session not found")
            session = self._by_id[session_id]

            if session.status != "open" and (cash_delta is not None or closing_amount is not None or status is not None):
                raise ValueError("only open cash sessions can be updated")

            if cash_delta is not None:
                session.expected_amount += cash_delta

            if closing_amount is not None:
                session.closing_amount = closing_amount
                session.difference_amount = closing_amount - session.expected_amount

            if status is not None:
                if status == "closed" and session.closing_amount is None:
                    raise ValueError("closing amount required")
                if status not in {"open", "closed"}:
                    raise ValueError("invalid cash session status")
                session.status = status
            return CashSession(**vars(session))

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            if session_id not in self._by_id:
                raise KeyError("cash session not found")
            del self._by_id[session_id]

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._seq = 0


cash_session_service = CashSessionService()
