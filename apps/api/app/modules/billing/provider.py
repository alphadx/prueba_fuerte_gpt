"""Provider contracts for electronic billing adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BillingEmissionRequest:
    company_id: str
    branch_id: str
    sale_id: str
    document_type: str
    totals: float
    idempotency_key: str


@dataclass(frozen=True)
class BillingEmissionResponse:
    provider_document_id: str
    track_id: str
    status: str
    folio: str
    xml_url: str
    pdf_url: str
    raw_payload_ref: str


class BillingProvider(Protocol):
    def emit(self, request: BillingEmissionRequest) -> BillingEmissionResponse:
        """Emit electronic tax document using provider transport."""

    def get_status(self, *, track_id: str) -> str:
        """Fetch provider/SII status for a previously emitted document."""
