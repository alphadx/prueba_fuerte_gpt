"""In-memory service layer for payments module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from app.modules.payments.cash_adapter import cash_payment_gateway
from app.modules.payments.gateway import PaymentChannel, PaymentIntent, PaymentStatus
from app.modules.payments.stub_adapters import gateway_registry


@dataclass
class Payment:
    id: str
    sale_id: str
    amount: float
    method: str
    status: str
    idempotency_key: str
    provider: str = "local"
    provider_payment_id: str | None = None
    branch_id: str | None = None
    channel: str | None = None
    currency: str = "CLP"


class PaymentService:
    def __init__(self) -> None:
        self._by_id: dict[str, Payment] = {}
        self._ids_by_idempotency_key: dict[str, str] = {}
        self._seq = 0
        self._lock = RLock()

    def list_payments(self) -> list[Payment]:
        with self._lock:
            return [Payment(**vars(item)) for item in self._by_id.values()]

    def create_payment(
        self,
        *,
        sale_id: str,
        amount: float,
        method: str,
        status: str,
        idempotency_key: str,
        provider: str = "local",
        provider_payment_id: str | None = None,
        branch_id: str | None = None,
        channel: str | None = None,
        currency: str = "CLP",
    ) -> Payment:
        with self._lock:
            if idempotency_key in self._ids_by_idempotency_key:
                raise ValueError("idempotency key already exists")

            self._seq += 1
            payment_id = f"pay-{self._seq:04d}"
            payment = Payment(
                id=payment_id,
                sale_id=sale_id,
                amount=amount,
                method=method,
                status=status,
                idempotency_key=idempotency_key,
                provider=provider,
                provider_payment_id=provider_payment_id,
                branch_id=branch_id,
                channel=channel,
                currency=currency,
            )
            self._by_id[payment_id] = payment
            self._ids_by_idempotency_key[idempotency_key] = payment_id
            return Payment(**vars(payment))


    def create_cash_payment(
        self,
        *,
        sale_id: str,
        amount: float,
        idempotency_key: str,
        company_id: str,
        branch_id: str,
        channel: str,
        currency: str = "CLP",
    ) -> Payment:
        with self._lock:
            if idempotency_key in self._ids_by_idempotency_key:
                raise ValueError("idempotency key already exists")

            intent = PaymentIntent(
                idempotency_key=idempotency_key,
                sale_id=sale_id,
                company_id=company_id,
                branch_id=branch_id,
                channel=PaymentChannel(channel),
                amount=amount,
                currency=currency,
                method="cash",
                metadata={},
            )
            result = cash_payment_gateway.authorize(intent)

            self._seq += 1
            payment_id = f"pay-{self._seq:04d}"
            payment = Payment(
                id=payment_id,
                sale_id=sale_id,
                amount=amount,
                method="cash",
                status=result.status.value,
                idempotency_key=idempotency_key,
                provider=result.provider,
                provider_payment_id=result.provider_payment_id,
                branch_id=branch_id,
                channel=channel,
                currency=currency,
            )
            self._by_id[payment_id] = payment
            self._ids_by_idempotency_key[idempotency_key] = payment_id
            return Payment(**vars(payment))


    def create_stub_payment(
        self,
        *,
        provider: str,
        sale_id: str,
        amount: float,
        idempotency_key: str,
        company_id: str,
        branch_id: str,
        channel: str,
        currency: str = "CLP",
        metadata: dict[str, str] | None = None,
    ) -> Payment:
        with self._lock:
            if provider not in gateway_registry:
                raise ValueError("unsupported provider")
            if idempotency_key in self._ids_by_idempotency_key:
                raise ValueError("idempotency key already exists")

            intent = PaymentIntent(
                idempotency_key=idempotency_key,
                sale_id=sale_id,
                company_id=company_id,
                branch_id=branch_id,
                channel=PaymentChannel(channel),
                amount=amount,
                currency=currency,
                method=provider,
                metadata=metadata or {},
            )

            gateway = gateway_registry[provider]
            authorized = gateway.authorize(intent)
            final_result = authorized
            if authorized.status == PaymentStatus.PENDING_CONFIRMATION:
                final_result = gateway.capture(intent)

            self._seq += 1
            payment_id = f"pay-{self._seq:04d}"
            payment = Payment(
                id=payment_id,
                sale_id=sale_id,
                amount=amount,
                method=provider,
                status=final_result.status.value,
                idempotency_key=idempotency_key,
                provider=final_result.provider,
                provider_payment_id=final_result.provider_payment_id,
                branch_id=branch_id,
                channel=channel,
                currency=currency,
            )
            self._by_id[payment_id] = payment
            self._ids_by_idempotency_key[idempotency_key] = payment_id
            return Payment(**vars(payment))

    def reconcile_cash_by_branch(self, *, branch_id: str) -> dict[str, int | float | str]:
        with self._lock:
            cash_items = [
                item
                for item in self._by_id.values()
                if item.method == "cash" and item.branch_id == branch_id
            ]
            approved = [item for item in cash_items if item.status in {"approved", "reconciled"}]
            pending = [item for item in cash_items if item.status not in {"approved", "reconciled"}]
            total_amount = sum(item.amount for item in cash_items)
            approved_amount = sum(item.amount for item in approved)
            return {
                "branch_id": branch_id,
                "payments_total": len(cash_items),
                "approved_total": len(approved),
                "pending_total": len(pending),
                "amount_total": round(total_amount, 2),
                "amount_approved": round(approved_amount, 2),
            }

    def get_payment(self, payment_id: str) -> Payment:
        with self._lock:
            if payment_id not in self._by_id:
                raise KeyError("payment not found")
            return Payment(**vars(self._by_id[payment_id]))

    def update_payment(self, payment_id: str, *, status: str | None) -> Payment:
        with self._lock:
            if payment_id not in self._by_id:
                raise KeyError("payment not found")
            payment = self._by_id[payment_id]
            if status is not None:
                payment.status = status
            return Payment(**vars(payment))

    def delete_payment(self, payment_id: str) -> None:
        with self._lock:
            payment = self.get_payment(payment_id)
            del self._by_id[payment_id]
            del self._ids_by_idempotency_key[payment.idempotency_key]

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_idempotency_key.clear()
            self._seq = 0


payment_service = PaymentService()
