"""In-memory service layer for payments module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass
class Payment:
    id: str
    sale_id: str
    amount: float
    method: str
    status: str
    idempotency_key: str


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
            )
            self._by_id[payment_id] = payment
            self._ids_by_idempotency_key[idempotency_key] = payment_id
            return Payment(**vars(payment))

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
