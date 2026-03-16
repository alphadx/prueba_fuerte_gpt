"""In-memory services for pickup e-commerce checkout and stock reservation."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from app.modules.products.service import ProductService, StockMovement, product_service

ORDER_TRANSITIONS: dict[str, str] = {
    "recibido": "preparado",
    "preparado": "listo_para_retiro",
    "listo_para_retiro": "entregado",
}


@dataclass
class OrderLine:
    product_id: str
    qty: float
    unit_price: float
    line_total: float


@dataclass
class OrderTransitionEvent:
    previous_state: str
    current_state: str
    actor: str
    reason: str


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
    transitions: list[OrderTransitionEvent]


@dataclass
class OrderObservabilitySnapshot:
    total_orders: int
    states: dict[str, int]
    delivered_orders: int
    rejected_checkouts: int
    rejected_transitions: int
    idempotent_replays: int


@dataclass
class OrderConsistencyReport:
    total_orders: int
    orders_with_inconsistencies: int
    inconsistencies: list[str]


class PickupOrderService:
    def __init__(self, *, product_service: ProductService) -> None:
        self._product_service = product_service
        self._by_id: dict[str, PickupOrder] = {}
        self._by_idempotency_key: dict[str, str] = {}
        self._seq = 0
        self._rejected_checkouts = 0
        self._rejected_transitions = 0
        self._idempotent_replays = 0
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
                self._idempotent_replays += 1
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
                transitions=[],
            )
            self._by_id[order_id] = order
            self._by_idempotency_key[idempotency_key] = order_id
            return self._clone(order)

    def get_order(self, order_id: str) -> PickupOrder:
        with self._lock:
            if order_id not in self._by_id:
                raise KeyError("order not found")
            return self._clone(self._by_id[order_id])

    def transition_order(
        self,
        *,
        order_id: str,
        target_state: str,
        actor: str,
        reason: str,
    ) -> PickupOrder:
        with self._lock:
            if order_id not in self._by_id:
                raise KeyError("order not found")

            order = self._by_id[order_id]
            if order.state == target_state:
                raise ValueError("order already in target state")

            expected_next_state = ORDER_TRANSITIONS.get(order.state)
            if expected_next_state is None or expected_next_state != target_state:
                raise ValueError("invalid order transition")

            previous_state = order.state
            order.state = target_state
            order.transitions.append(
                OrderTransitionEvent(
                    previous_state=previous_state,
                    current_state=target_state,
                    actor=actor,
                    reason=reason,
                )
            )
            return self._clone(order)

    def register_checkout_rejection(self) -> None:
        with self._lock:
            self._rejected_checkouts += 1

    def register_transition_rejection(self) -> None:
        with self._lock:
            self._rejected_transitions += 1

    def get_observability_snapshot(self) -> OrderObservabilitySnapshot:
        with self._lock:
            states: dict[str, int] = {}
            for order in self._by_id.values():
                states[order.state] = states.get(order.state, 0) + 1

            return OrderObservabilitySnapshot(
                total_orders=len(self._by_id),
                states=states,
                delivered_orders=states.get("entregado", 0),
                rejected_checkouts=self._rejected_checkouts,
                rejected_transitions=self._rejected_transitions,
                idempotent_replays=self._idempotent_replays,
            )

    def run_consistency_report(self) -> OrderConsistencyReport:
        with self._lock:
            inconsistencies: list[str] = []
            movements = self._product_service.list_stock_movements()
            movements_by_reference: dict[str, list[StockMovement]] = {}
            for movement in movements:
                movements_by_reference.setdefault(movement.reference_id, []).append(movement)

            for order in self._by_id.values():
                reference_movements = movements_by_reference.get(order.order_id, [])
                if len(reference_movements) != len(order.lines):
                    inconsistencies.append(
                        f"{order.order_id}: expected {len(order.lines)} stock movements, found {len(reference_movements)}"
                    )
                    continue

                expected_by_product = {line.product_id: -line.qty for line in order.lines}
                for movement in reference_movements:
                    expected_qty = expected_by_product.get(movement.product_id)
                    if expected_qty is None:
                        inconsistencies.append(
                            f"{order.order_id}: unexpected movement product {movement.product_id}"
                        )
                        continue
                    if movement.quantity_delta != expected_qty:
                        inconsistencies.append(
                            f"{order.order_id}: product {movement.product_id} expected delta {expected_qty}, got {movement.quantity_delta}"
                        )
                    if movement.reason != "pickup-checkout-confirmation":
                        inconsistencies.append(
                            f"{order.order_id}: invalid movement reason {movement.reason}"
                        )

            return OrderConsistencyReport(
                total_orders=len(self._by_id),
                orders_with_inconsistencies=len(inconsistencies),
                inconsistencies=inconsistencies,
            )

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._by_idempotency_key.clear()
            self._seq = 0
            self._rejected_checkouts = 0
            self._rejected_transitions = 0
            self._idempotent_replays = 0

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
            transitions=[OrderTransitionEvent(**vars(item)) for item in order.transitions],
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
