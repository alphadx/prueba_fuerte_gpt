"""In-memory service for POS sale completion flow with cash and stock impact."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from threading import RLock

from app.modules.cash_sessions.service import cash_session_service
from app.modules.products.service import ProductService, product_service
from app.services.queue import queue_client

TWOPLACES = Decimal("0.01")


@dataclass
class SaleLine:
    product_id: str
    quantity: float
    unit_price: float
    line_subtotal: float
    line_tax: float
    line_total: float


@dataclass
class Sale:
    id: str
    branch_id: str
    cash_session_id: str
    sold_by: str
    status: str
    subtotal: float
    taxes: float
    total: float
    payment_method: str
    payment_status: str
    lines: list[SaleLine]
    billing_event_emitted: bool


class SaleService:
    def __init__(self, *, product_service: ProductService) -> None:
        self._product_service = product_service
        self._by_id: dict[str, Sale] = {}
        self._seq = 0
        self._lock = RLock()

    def list_sales(self) -> list[Sale]:
        with self._lock:
            return [self._clone(item) for item in self._by_id.values()]

    def complete_sale(
        self,
        *,
        branch_id: str,
        cash_session_id: str,
        sold_by: str,
        payment_method: str,
        lines_payload: list[dict[str, float | str]],
        tax_rate: float = 0.19,
    ) -> Sale:
        if payment_method not in {"cash", "card_stub", "wallet_stub"}:
            raise ValueError("unsupported payment method")
        if not lines_payload:
            raise ValueError("sale requires at least one line")

        session = cash_session_service.get_session(cash_session_id)
        if session.status != "open":
            raise ValueError("cash session must be open")
        if session.branch_id != branch_id:
            raise ValueError("cash session branch mismatch")

        with self._lock:
            built_lines: list[SaleLine] = []
            for payload in lines_payload:
                product_id = str(payload["product_id"])
                quantity = float(payload["quantity"])
                if quantity <= 0:
                    raise ValueError("line quantity must be positive")
                product = self._product_service.get_product(product_id)
                unit_price = float(product.price)
                line_subtotal = self._money(unit_price * quantity)
                line_tax = self._money(line_subtotal * tax_rate)
                line_total = self._money(line_subtotal + line_tax)
                built_lines.append(
                    SaleLine(
                        product_id=product_id,
                        quantity=quantity,
                        unit_price=unit_price,
                        line_subtotal=line_subtotal,
                        line_tax=line_tax,
                        line_total=line_total,
                    )
                )

            subtotal = self._money(sum(line.line_subtotal for line in built_lines))
            taxes = self._money(sum(line.line_tax for line in built_lines))
            total = self._money(subtotal + taxes)

            self._seq += 1
            sale_id = f"sale-{self._seq:04d}"

            movements = []
            try:
                for line in built_lines:
                    movement = self._product_service.decrement_stock(
                        product_id=line.product_id,
                        quantity=line.quantity,
                        reason="sale-confirmation",
                        reference_id=sale_id,
                    )
                    movements.append(movement)
            except Exception as exc:
                for movement in reversed(movements):
                    current = self._product_service.get_stock(movement.product_id)
                    self._product_service.set_stock(movement.product_id, current + abs(movement.quantity_delta))
                raise ValueError("stock update failed; sale rolled back") from exc

            payment_status = "approved" if payment_method == "cash" else "pending"

            sale = Sale(
                id=sale_id,
                branch_id=branch_id,
                cash_session_id=cash_session_id,
                sold_by=sold_by,
                status="paid" if payment_status == "approved" else "confirmed",
                subtotal=subtotal,
                taxes=taxes,
                total=total,
                payment_method=payment_method,
                payment_status=payment_status,
                lines=built_lines,
                billing_event_emitted=False,
            )
            self._by_id[sale_id] = sale

            backend = queue_client.enqueue_alert(
                {
                    "event_type": "billing.sale_confirmed",
                    "sale_id": sale.id,
                    "branch_id": sale.branch_id,
                    "total": sale.total,
                }
            )
            sale.billing_event_emitted = True
            if backend:
                return self._clone(sale)
            return self._clone(sale)

    def _clone(self, sale: Sale) -> Sale:
        return Sale(
            id=sale.id,
            branch_id=sale.branch_id,
            cash_session_id=sale.cash_session_id,
            sold_by=sale.sold_by,
            status=sale.status,
            subtotal=sale.subtotal,
            taxes=sale.taxes,
            total=sale.total,
            payment_method=sale.payment_method,
            payment_status=sale.payment_status,
            lines=[SaleLine(**vars(item)) for item in sale.lines],
            billing_event_emitted=sale.billing_event_emitted,
        )

    @staticmethod
    def _money(value: float) -> float:
        return float(Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP))

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._seq = 0


sale_service = SaleService(product_service=product_service)
