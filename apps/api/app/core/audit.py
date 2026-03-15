"""Simple audit sink for critical operations during MVP."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("audit")


def record_audit_event(*, actor_id: str, action: str, entity: str, metadata: dict[str, Any]) -> None:
    """Emit structured audit logs for traceability-sensitive actions."""
    logger.info(
        "audit_event actor_id=%s action=%s entity=%s metadata=%s",
        actor_id,
        action,
        entity,
        metadata,
    )
