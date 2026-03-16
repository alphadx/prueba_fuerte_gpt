"""In-memory alert evaluation engine for HR document expirations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from threading import RLock

from app.modules.employee_documents.service import EmployeeDocument


@dataclass
class AlarmEvent:
    id: str
    employee_document_id: str
    employee_id: str
    document_type_code: str
    threshold_days: int
    days_to_expire: int
    evaluation_date: str
    status: str


class AlarmEventService:
    def __init__(self) -> None:
        self._by_id: dict[str, AlarmEvent] = {}
        self._ids_by_key: dict[tuple[str, int, str], str] = {}
        self._seq = 0
        self._lock = RLock()

    def list_events(self) -> list[AlarmEvent]:
        with self._lock:
            return [AlarmEvent(**vars(item)) for item in self._by_id.values()]

    def evaluate_documents(
        self,
        *,
        documents: list[EmployeeDocument],
        evaluation_date: str,
        thresholds: tuple[int, ...] = (30, 15, 7, 1),
    ) -> list[AlarmEvent]:
        today = date.fromisoformat(evaluation_date)
        created_events: list[AlarmEvent] = []

        with self._lock:
            for doc in documents:
                expiry = date.fromisoformat(doc.expires_on)
                days_to_expire = (expiry - today).days
                if days_to_expire < 0:
                    continue
                if days_to_expire not in thresholds:
                    continue

                dedupe_key = (doc.id, days_to_expire, evaluation_date)
                if dedupe_key in self._ids_by_key:
                    continue

                self._seq += 1
                event_id = f"alarm-{self._seq:04d}"
                event = AlarmEvent(
                    id=event_id,
                    employee_document_id=doc.id,
                    employee_id=doc.employee_id,
                    document_type_code=doc.document_type_code,
                    threshold_days=days_to_expire,
                    days_to_expire=days_to_expire,
                    evaluation_date=evaluation_date,
                    status="pending",
                )
                self._by_id[event_id] = event
                self._ids_by_key[dedupe_key] = event_id
                created_events.append(AlarmEvent(**vars(event)))

        return created_events

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_key.clear()
            self._seq = 0


alarm_event_service = AlarmEventService()
