"""In-memory billing orchestration with async emission queue and retries."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from app.modules.billing.provider import BillingEmissionRequest, BillingProvider
from app.modules.billing.sandbox_adapter import SandboxBillingProvider


@dataclass
class BillingDocument:
    sale_id: str
    company_id: str
    branch_id: str
    totals: float
    idempotency_key: str
    document_type: str
    status: str
    attempts: int
    max_attempts: int
    provider_document_id: str | None = None
    track_id: str | None = None
    folio: str | None = None
    xml_url: str | None = None
    pdf_url: str | None = None
    raw_payload_ref: str | None = None
    sii_status: str | None = None
    last_error: str | None = None


@dataclass
class BillingEmissionEvent:
    sale_id: str
    company_id: str
    branch_id: str
    total: float
    document_type: str


class BillingService:
    def __init__(self, *, provider: BillingProvider, max_attempts: int = 3) -> None:
        self._provider = provider
        self._max_attempts = max_attempts
        self._lock = RLock()
        self._documents: dict[tuple[str, str], BillingDocument] = {}
        self._emission_queue: list[BillingEmissionEvent] = []
        self._queued_index: dict[tuple[str, str], BillingEmissionEvent] = {}

    def enqueue_sale_emission_event(
        self,
        *,
        sale_id: str,
        branch_id: str,
        total: float,
        company_id: str = "company-001",
        document_type: str = "boleta",
    ) -> BillingEmissionEvent:
        with self._lock:
            key = (sale_id, document_type)
            if key in self._documents:
                doc = self._documents[key]
                return BillingEmissionEvent(
                    sale_id=doc.sale_id,
                    company_id=doc.company_id,
                    branch_id=doc.branch_id,
                    total=doc.totals,
                    document_type=doc.document_type,
                )

            existing = self._queued_index.get(key)
            if existing is not None:
                return BillingEmissionEvent(**vars(existing))

            event = BillingEmissionEvent(
                sale_id=sale_id,
                company_id=company_id,
                branch_id=branch_id,
                total=total,
                document_type=document_type,
            )
            self._emission_queue.append(event)
            self._queued_index[key] = event
            return BillingEmissionEvent(**vars(event))

    def enqueue_sale_document(
        self,
        *,
        sale_id: str,
        branch_id: str,
        total: float,
        company_id: str = "company-001",
        document_type: str = "boleta",
    ) -> BillingDocument:
        """Backward-compatible direct enqueue (used in tests/prototype helpers)."""
        with self._lock:
            key = (sale_id, document_type)
            existing = self._documents.get(key)
            if existing is not None:
                return self._clone(existing)

            doc = self._build_queued_document(
                sale_id=sale_id,
                company_id=company_id,
                branch_id=branch_id,
                total=total,
                document_type=document_type,
            )
            self._documents[key] = doc
            return self._clone(doc)

    def get_by_sale_id(self, sale_id: str, *, document_type: str = "boleta") -> BillingDocument:
        with self._lock:
            key = (sale_id, document_type)
            found = self._documents.get(key)
            if found is not None:
                return self._clone(found)

            queued = self._queued_index.get(key)
            if queued is not None:
                placeholder = self._build_queued_document(
                    sale_id=queued.sale_id,
                    company_id=queued.company_id,
                    branch_id=queued.branch_id,
                    total=queued.total,
                    document_type=queued.document_type,
                )
                return placeholder

            raise KeyError("billing document not found")

    def process_worker_batch(self, *, limit: int = 20) -> tuple[int, int, int, int]:
        enqueued = self.drain_emission_events(limit=limit)
        processed, succeeded, failed = self.process_pending(limit=limit)
        return enqueued, processed, succeeded, failed

    def drain_emission_events(self, *, limit: int = 20) -> int:
        with self._lock:
            if limit <= 0:
                return 0

            to_drain = self._emission_queue[:limit]
            self._emission_queue = self._emission_queue[limit:]

            drained = 0
            for event in to_drain:
                key = (event.sale_id, event.document_type)
                self._queued_index.pop(key, None)
                if key in self._documents:
                    continue
                self._documents[key] = self._build_queued_document(
                    sale_id=event.sale_id,
                    company_id=event.company_id,
                    branch_id=event.branch_id,
                    total=event.total,
                    document_type=event.document_type,
                )
                drained += 1
            return drained

    def process_pending(self, *, limit: int = 20) -> tuple[int, int, int]:
        with self._lock:
            pending_keys = [
                key
                for key, doc in self._documents.items()
                if doc.status in {"queued", "retryable_error"}
            ][:limit]

        processed = succeeded = failed = 0
        for key in pending_keys:
            processed += 1
            if self._process_one(key=key):
                succeeded += 1
            else:
                failed += 1

        return processed, succeeded, failed

    def _process_one(self, *, key: tuple[str, str]) -> bool:
        with self._lock:
            doc = self._documents[key]
            if doc.status not in {"queued", "retryable_error"}:
                return True
            if doc.attempts >= doc.max_attempts:
                doc.status = "failed"
                return False

            doc.status = "processing"
            doc.attempts += 1
            request = BillingEmissionRequest(
                company_id=doc.company_id,
                branch_id=doc.branch_id,
                sale_id=doc.sale_id,
                document_type=doc.document_type,
                totals=doc.totals,
                idempotency_key=doc.idempotency_key,
            )

        try:
            response = self._provider.emit(request)
        except Exception as exc:
            with self._lock:
                doc = self._documents[key]
                doc.last_error = str(exc)
                doc.status = "failed" if doc.attempts >= doc.max_attempts else "retryable_error"
            return False

        with self._lock:
            doc = self._documents[key]
            doc.provider_document_id = response.provider_document_id
            doc.track_id = response.track_id
            doc.status = response.status
            doc.folio = response.folio
            doc.xml_url = response.xml_url
            doc.pdf_url = response.pdf_url
            doc.raw_payload_ref = response.raw_payload_ref
            doc.sii_status = self._provider.get_status(track_id=response.track_id)
            doc.last_error = None
        return True

    def reset_state(self) -> None:
        with self._lock:
            self._documents.clear()
            self._emission_queue.clear()
            self._queued_index.clear()

        reset_provider = getattr(self._provider, "reset_state", None)
        if callable(reset_provider):
            reset_provider()

    def _build_queued_document(
        self,
        *,
        sale_id: str,
        company_id: str,
        branch_id: str,
        total: float,
        document_type: str,
    ) -> BillingDocument:
        return BillingDocument(
            sale_id=sale_id,
            company_id=company_id,
            branch_id=branch_id,
            totals=total,
            idempotency_key=f"{sale_id}:{document_type}",
            document_type=document_type,
            status="queued",
            attempts=0,
            max_attempts=self._max_attempts,
        )

    @staticmethod
    def _clone(doc: BillingDocument) -> BillingDocument:
        return BillingDocument(**vars(doc))


billing_service = BillingService(provider=SandboxBillingProvider())
