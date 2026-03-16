"""Notification dispatch service for alert events (in-app + email in test env)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock

from app.modules.alerts.service import AlarmEvent


@dataclass
class NotificationAttempt:
    id: str
    event_id: str
    channel: str
    status: str
    detail: str
    attempted_at: str


class AlertNotificationService:
    def __init__(self) -> None:
        self._by_id: dict[str, NotificationAttempt] = {}
        self._seq = 0
        self._lock = RLock()

    def list_attempts(self) -> list[NotificationAttempt]:
        with self._lock:
            return [NotificationAttempt(**vars(item)) for item in self._by_id.values()]

    def dispatch_event(self, *, event: AlarmEvent, channels: tuple[str, ...] = ("in_app", "email")) -> list[NotificationAttempt]:
        attempts: list[NotificationAttempt] = []
        now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        for channel in channels:
            status, detail = self._deliver(channel=channel, event=event)
            with self._lock:
                self._seq += 1
                attempt_id = f"notify-{self._seq:04d}"
                attempt = NotificationAttempt(
                    id=attempt_id,
                    event_id=event.id,
                    channel=channel,
                    status=status,
                    detail=detail,
                    attempted_at=now,
                )
                self._by_id[attempt_id] = attempt
                attempts.append(NotificationAttempt(**vars(attempt)))

        return attempts

    def _deliver(self, *, channel: str, event: AlarmEvent) -> tuple[str, str]:
        if channel == "in_app":
            return "sent", "in_app notification stored"

        if channel == "email":
            # Simulación entorno pruebas: si snapshot incluye force_email_fail, se marca failed.
            if bool(event.rule_snapshot.get("force_email_fail", False)):
                return "failed", "simulated email channel failure"
            return "sent", "email accepted by test adapter"

        return "failed", f"unsupported channel: {channel}"

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._seq = 0


alert_notification_service = AlertNotificationService()
