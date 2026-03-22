"""In-memory alert evaluation engine for HR document expirations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
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
    dedupe_key: str
    status: str
    source: str
    generated_at: str
    rule_snapshot: dict[str, object]
    notification_statuses: dict[str, str]


@dataclass
class AlertEvaluationRun:
    id: str
    evaluation_date: str
    thresholds: tuple[int, ...]
    scanned_documents: int
    matched_documents: int
    duplicate_events: int
    expired_documents: int
    generated_events: int
    created_at: str


@dataclass
class AlertEvaluationResult:
    events: list[AlarmEvent]
    run: AlertEvaluationRun


@dataclass
class AlertsSummary:
    total_events: int
    pending_events: int
    sent_events: int
    partially_failed_events: int
    failed_events: int
    total_notification_attempts: int
    sent_notification_attempts: int
    failed_notification_attempts: int
    total_evaluations: int


class AlarmEventService:
    def __init__(self) -> None:
        self._by_id: dict[str, AlarmEvent] = {}
        self._ids_by_key: dict[tuple[str, int, str], str] = {}
        self._runs_by_id: dict[str, AlertEvaluationRun] = {}
        self._event_seq = 0
        self._run_seq = 0
        self._lock = RLock()

    def list_events(self) -> list[AlarmEvent]:
        with self._lock:
            return [AlarmEvent(**vars(item)) for item in self._by_id.values()]

    def list_runs(self) -> list[AlertEvaluationRun]:
        with self._lock:
            return [AlertEvaluationRun(**vars(item)) for item in self._runs_by_id.values()]

    def list_dispatchable_events(self) -> list[AlarmEvent]:
        with self._lock:
            return [
                AlarmEvent(**vars(item))
                for item in self._by_id.values()
                if item.status in {"pending", "partially_failed", "failed"}
            ]

    def update_notification_status(self, *, event_id: str, channel: str, status: str) -> AlarmEvent:
        with self._lock:
            if event_id not in self._by_id:
                raise KeyError("alarm event not found")
            event = self._by_id[event_id]
            event.notification_statuses[channel] = status
            channel_states = set(event.notification_statuses.values())
            if "failed" in channel_states:
                event.status = "partially_failed" if "sent" in channel_states else "failed"
            elif channel_states and channel_states == {"sent"}:
                event.status = "sent"
            return AlarmEvent(**vars(event))

    def evaluate_documents(
        self,
        *,
        documents: list[EmployeeDocument],
        evaluation_date: str,
        thresholds: tuple[int, ...] = (30, 15, 7, 1),
    ) -> AlertEvaluationResult:
        today = date.fromisoformat(evaluation_date)
        now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        created_events: list[AlarmEvent] = []
        matched_documents = 0
        duplicate_events = 0
        expired_documents = 0

        with self._lock:
            for doc in documents:
                expiry = date.fromisoformat(doc.expires_on)
                days_to_expire = (expiry - today).days
                if days_to_expire < 0:
                    expired_documents += 1
                    continue
                if days_to_expire not in thresholds:
                    continue

                matched_documents += 1
                dedupe_key = (doc.id, days_to_expire, evaluation_date)
                if dedupe_key in self._ids_by_key:
                    duplicate_events += 1
                    continue

                self._event_seq += 1
                event_id = f"alarm-{self._event_seq:04d}"
                event = AlarmEvent(
                    id=event_id,
                    employee_document_id=doc.id,
                    employee_id=doc.employee_id,
                    document_type_code=doc.document_type_code,
                    threshold_days=days_to_expire,
                    days_to_expire=days_to_expire,
                    evaluation_date=evaluation_date,
                    dedupe_key=f"{doc.id}:{days_to_expire}:{evaluation_date}",
                    status="pending",
                    source="daily_evaluator",
                    generated_at=now,
                    rule_snapshot={"threshold_days": days_to_expire, "evaluation_date": evaluation_date},
                    notification_statuses={},
                )
                self._by_id[event_id] = event
                self._ids_by_key[dedupe_key] = event_id
                created_events.append(AlarmEvent(**vars(event)))

            self._run_seq += 1
            run_id = f"eval-{self._run_seq:04d}"
            run = AlertEvaluationRun(
                id=run_id,
                evaluation_date=evaluation_date,
                thresholds=thresholds,
                scanned_documents=len(documents),
                matched_documents=matched_documents,
                duplicate_events=duplicate_events,
                expired_documents=expired_documents,
                generated_events=len(created_events),
                created_at=now,
            )
            self._runs_by_id[run_id] = run

        return AlertEvaluationResult(events=created_events, run=AlertEvaluationRun(**vars(run)))

    def summarize(self, *, notification_attempts: list[tuple[str, str]]) -> AlertsSummary:
        with self._lock:
            events = list(self._by_id.values())
            return AlertsSummary(
                total_events=len(events),
                pending_events=sum(1 for event in events if event.status == "pending"),
                sent_events=sum(1 for event in events if event.status == "sent"),
                partially_failed_events=sum(1 for event in events if event.status == "partially_failed"),
                failed_events=sum(1 for event in events if event.status == "failed"),
                total_notification_attempts=len(notification_attempts),
                sent_notification_attempts=sum(1 for _, status in notification_attempts if status == "sent"),
                failed_notification_attempts=sum(1 for _, status in notification_attempts if status != "sent"),
                total_evaluations=len(self._runs_by_id),
            )

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_key.clear()
            self._runs_by_id.clear()
            self._event_seq = 0
            self._run_seq = 0


alarm_event_service = AlarmEventService()
