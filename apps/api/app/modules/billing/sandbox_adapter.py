"""Sandbox adapter for electronic billing provider."""

from __future__ import annotations

import hashlib
import os

from app.modules.billing.provider import BillingEmissionRequest, BillingEmissionResponse


class SandboxBillingProvider:
    """Deterministic sandbox provider to emulate boleta issuance lifecycle."""

    def emit(self, request: BillingEmissionRequest) -> BillingEmissionResponse:
        force_error = os.getenv("BILLING_SANDBOX_FORCE_ERROR", "false").lower() == "true"
        if force_error:
            raise RuntimeError("sandbox provider temporary error")

        seed = f"{request.sale_id}:{request.idempotency_key}".encode()
        digest = hashlib.sha1(seed).hexdigest()
        folio = str(int(digest[:8], 16) % 900000 + 100000)
        track_id = f"track-{digest[:12]}"
        provider_document_id = f"sandbox-doc-{digest[12:24]}"
        base = os.getenv("BILLING_SANDBOX_ASSET_BASE", "https://sandbox.billing.local")

        return BillingEmissionResponse(
            provider_document_id=provider_document_id,
            track_id=track_id,
            status="accepted",
            folio=folio,
            xml_url=f"{base}/xml/{provider_document_id}.xml",
            pdf_url=f"{base}/pdf/{provider_document_id}.pdf",
            raw_payload_ref=f"sandbox://payloads/{provider_document_id}",
        )

    def get_status(self, *, track_id: str) -> str:
        if track_id.startswith("track-"):
            return "accepted"
        return "unknown"
