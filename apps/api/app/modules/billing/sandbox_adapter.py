"""Sandbox adapter for electronic billing provider."""

from __future__ import annotations

import hashlib
import os
from threading import RLock

from app.modules.billing.provider import BillingEmissionRequest, BillingEmissionResponse

_ALLOWED_STATUSES = {"accepted", "processing", "rejected"}
# SII referencia (marco general de facturación electrónica):
# - https://www.sii.cl/servicios_online/1039-.html
# - https://www.sii.cl/factura_electronica/form_ele.htm
# En prototipo usamos estados canónicos simplificados para pruebas.


class SandboxBillingProvider:
    """Deterministic sandbox provider to emulate boleta issuance lifecycle.

    Config knobs (env vars):
    - BILLING_SANDBOX_FORCE_ERROR=true: always fail emission.
    - BILLING_SANDBOX_FAIL_FIRST_N=<int>: fail first N attempts per idempotency key.
    - BILLING_SANDBOX_EMIT_STATUS=accepted|processing|rejected: initial emit status.
    - BILLING_SANDBOX_STATUS_MODE=stable|progressive: progressive turns processing -> accepted.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._attempts_by_idempotency: dict[str, int] = {}
        self._status_by_track_id: dict[str, str] = {}
        self._status_queries: dict[str, int] = {}

    def emit(self, request: BillingEmissionRequest) -> BillingEmissionResponse:
        self._register_attempt(request.idempotency_key)

        force_error = os.getenv("BILLING_SANDBOX_FORCE_ERROR", "false").lower() == "true"
        fail_first_n = int(os.getenv("BILLING_SANDBOX_FAIL_FIRST_N", "0"))
        if force_error or self._attempts_for(request.idempotency_key) <= fail_first_n:
            raise RuntimeError("sandbox provider temporary error")

        seed = f"{request.company_id}:{request.branch_id}:{request.sale_id}:{request.document_type}:{request.idempotency_key}".encode()
        digest = hashlib.sha1(seed).hexdigest()
        folio = str(int(digest[:8], 16) % 900000 + 100000)
        track_id = f"track-{digest[:12]}"
        provider_document_id = f"sandbox-doc-{digest[12:24]}"
        base = os.getenv("BILLING_SANDBOX_ASSET_BASE", "https://sandbox.billing.local")

        status = os.getenv("BILLING_SANDBOX_EMIT_STATUS", "accepted").lower()
        if status not in _ALLOWED_STATUSES:
            status = "accepted"

        with self._lock:
            self._status_by_track_id[track_id] = status

        return BillingEmissionResponse(
            provider_document_id=provider_document_id,
            track_id=track_id,
            status=status,
            folio=folio,
            xml_url=f"{base}/xml/{provider_document_id}.xml",
            pdf_url=f"{base}/pdf/{provider_document_id}.pdf",
            raw_payload_ref=f"sandbox://payloads/{request.company_id}/{request.branch_id}/{provider_document_id}",
        )

    def get_status(self, *, track_id: str) -> str:
        with self._lock:
            stored = self._status_by_track_id.get(track_id)
            if stored is None:
                return "unknown"
            self._status_queries[track_id] = self._status_queries.get(track_id, 0) + 1
            status_mode = os.getenv("BILLING_SANDBOX_STATUS_MODE", "stable").lower()
            # Simulación controlada para reconciliación asincrónica: estado intermedio -> aceptado.
            if status_mode == "progressive" and stored == "processing" and self._status_queries[track_id] >= 2:
                self._status_by_track_id[track_id] = "accepted"
                return "accepted"
            return stored

    def reset_state(self) -> None:
        with self._lock:
            self._attempts_by_idempotency.clear()
            self._status_by_track_id.clear()
            self._status_queries.clear()

    def _register_attempt(self, idempotency_key: str) -> None:
        with self._lock:
            self._attempts_by_idempotency[idempotency_key] = self._attempts_by_idempotency.get(idempotency_key, 0) + 1

    def _attempts_for(self, idempotency_key: str) -> int:
        with self._lock:
            return self._attempts_by_idempotency.get(idempotency_key, 0)
