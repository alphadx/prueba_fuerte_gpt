"""In-memory services for pickup e-commerce checkout and stock reservation."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from app.modules.products.service import ProductService, product_service


@dataclass
class OrderLine:
    product_id: str
    qty: float
    unit_price: float
    line_total: float


@dataclass
class PickupOrder:
    order_id: str
    state: str
    branch_id: str
    pickup_slot_id: str
    customer: dict[str, str]
    idempotency_key: str
    lines: list[OrderLine]
    subtotal: float


class PickupOrderService:
    def __init__(self, *, product_service: ProductService) -> None:
        self._product_service = product_service
        self._by_id: dict[str, PickupOrder] = {}
        self._by_idempotency_key: dict[str, str] = {}
        self._seq = 0
        self._lock = RLock()

    def create_order(
        self,
        *,
        branch_id: str,
        pickup_slot_id: str,
        customer: dict[str, str],
        lines_payload: list[dict[str, float | str]],
        idempotency_key: str,
    ) -> PickupOrder:
        if not lines_payload:
            raise ValueError("checkout requires at least one line")

        with self._lock:
            existing_id = self._by_idempotency_key.get(idempotency_key)
            if existing_id:
                return self._clone(self._by_id[existing_id])

            built_lines: list[OrderLine] = []
            for payload in lines_payload:
                product_id = str(payload["product_id"])
                qty = float(payload["qty"])
                if qty <= 0:
                    raise ValueError("line quantity must be positive")

                product = self._product_service.get_product(product_id)
                unit_price = float(product.price)
                built_lines.append(
                    OrderLine(
                        product_id=product_id,
                        qty=qty,
                        unit_price=unit_price,
                        line_total=unit_price * qty,
                    )
                )

            self._seq += 1
            order_id = f"ord-{self._seq:04d}"

            try:
                for line in built_lines:
                    self._product_service.decrement_stock(
                        product_id=line.product_id,
                        quantity=line.qty,
                        reason="pickup-checkout-confirmation",
                        reference_id=order_id,
                    )
            except Exception as exc:
                self._product_service.rollback_reference(reference_id=order_id)
                raise ValueError("insufficient stock at confirmation") from exc

            subtotal = sum(line.line_total for line in built_lines)
            order = PickupOrder(
                order_id=order_id,
                state="recibido",
                branch_id=branch_id,
                pickup_slot_id=pickup_slot_id,
                customer=customer,
                idempotency_key=idempotency_key,
                lines=built_lines,
                subtotal=subtotal,
            )
            self._by_id[order_id] = order
            self._by_idempotency_key[idempotency_key] = order_id
            return self._clone(order)

    def get_order(self, order_id: str) -> PickupOrder:
        with self._lock:
            if order_id not in self._by_id:
                raise KeyError("order not found")
            return self._clone(self._by_id[order_id])

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._by_idempotency_key.clear()
            self._seq = 0

    @staticmethod
    def _clone(order: PickupOrder) -> PickupOrder:
        return PickupOrder(
            order_id=order.order_id,
            state=order.state,
            branch_id=order.branch_id,
            pickup_slot_id=order.pickup_slot_id,
            customer=dict(order.customer),
            idempotency_key=order.idempotency_key,
            lines=[OrderLine(**vars(line)) for line in order.lines],
            subtotal=order.subtotal,
        )


pickup_order_service = PickupOrderService(product_service=product_service)


class CatalogService:
    def __init__(self, *, product_service: ProductService) -> None:
        self._product_service = product_service

    def list_products_by_branch(self, branch_id: str) -> list[dict[str, object]]:
        if not branch_id:
            raise ValueError("invalid branch")

        products = []
        for product in self._product_service.list_products():
            products.append(
                {
                    "product_id": product.id,
                    "sku": product.sku,
                    "name": product.name,
                    "price": float(product.price),
                    "currency": "CLP",
                    "available_stock": self._product_service.get_stock(product.id),
                    "branch_id": branch_id,
                    "is_pickup_enabled": True,
                }
            )
        return products


catalog_service = CatalogService(product_service=product_service)


class PickupSlotService:
    _slots_by_branch = {
        "br-001": [
            {"pickup_slot_id": "slot-10-11", "start_at": "10:00", "end_at": "11:00", "status": "available", "remaining_capacity": 10},
            {"pickup_slot_id": "slot-11-12", "start_at": "11:00", "end_at": "12:00", "status": "available", "remaining_capacity": 8},
        ],
        "br-002": [
            {"pickup_slot_id": "slot-09-10", "start_at": "09:00", "end_at": "10:00", "status": "available", "remaining_capacity": 12},
        ],
    }

    def list_slots(self, *, branch_id: str, date: str) -> dict[str, object]:
        slots = self._slots_by_branch.get(branch_id)
        if slots is None:
            raise KeyError("no slots configured")
        return {"branch_id": branch_id, "date": date, "slots": slots}


pickup_slot_service = PickupSlotService()
