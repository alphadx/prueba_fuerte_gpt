"""In-memory service layer for products module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass
class Product:
    id: str
    sku: str
    name: str
    price: float


@dataclass
class StockMovement:
    id: str
    product_id: str
    movement_type: str
    quantity_delta: float
    reason: str
    reference_id: str


class ProductService:
    """Application service encapsulating product CRUD rules."""

    def __init__(self) -> None:
        self._by_id: dict[str, Product] = {}
        self._ids_by_sku: dict[str, str] = {}
        self._stock_by_product_id: dict[str, float] = {}
        self._movements: list[StockMovement] = []
        self._seq = 0
        self._movement_seq = 0
        self._lock = RLock()

    def list_products(self) -> list[Product]:
        with self._lock:
            return [Product(**vars(item)) for item in self._by_id.values()]

    def create_product(self, *, sku: str, name: str, price: float) -> Product:
        with self._lock:
            if sku in self._ids_by_sku:
                raise ValueError("sku already exists")

            self._seq += 1
            product_id = f"prod-{self._seq:04d}"
            product = Product(id=product_id, sku=sku, name=name, price=price)
            self._by_id[product_id] = product
            self._ids_by_sku[sku] = product_id
            self._stock_by_product_id[product_id] = 0.0
            return product

    def set_stock(self, product_id: str, quantity: float) -> float:
        with self._lock:
            if product_id not in self._by_id:
                raise KeyError("product not found")
            if quantity < 0:
                raise ValueError("stock cannot be negative")
            self._stock_by_product_id[product_id] = quantity
            return quantity

    def get_stock(self, product_id: str) -> float:
        with self._lock:
            if product_id not in self._by_id:
                raise KeyError("product not found")
            return self._stock_by_product_id.get(product_id, 0.0)

    def decrement_stock(self, *, product_id: str, quantity: float, reason: str, reference_id: str) -> StockMovement:
        with self._lock:
            if product_id not in self._by_id:
                raise KeyError("product not found")
            if quantity <= 0:
                raise ValueError("quantity must be positive")

            current = self._stock_by_product_id.get(product_id, 0.0)
            if current < quantity:
                raise ValueError("insufficient stock")

            self._stock_by_product_id[product_id] = current - quantity
            self._movement_seq += 1
            movement = StockMovement(
                id=f"mov-{self._movement_seq:04d}",
                product_id=product_id,
                movement_type="outbound",
                quantity_delta=-quantity,
                reason=reason,
                reference_id=reference_id,
            )
            self._movements.append(movement)
            return StockMovement(**vars(movement))

    def list_stock_movements(self) -> list[StockMovement]:
        with self._lock:
            return [StockMovement(**vars(item)) for item in self._movements]


    def rollback_reference(self, *, reference_id: str) -> None:
        with self._lock:
            kept: list[StockMovement] = []
            rolled_back: list[StockMovement] = []
            for movement in self._movements:
                if movement.reference_id == reference_id:
                    rolled_back.append(movement)
                else:
                    kept.append(movement)

            for movement in rolled_back:
                if movement.product_id in self._stock_by_product_id:
                    self._stock_by_product_id[movement.product_id] = (
                        self._stock_by_product_id[movement.product_id] - movement.quantity_delta
                    )

            self._movements = kept

    def get_product(self, product_id: str) -> Product:
        with self._lock:
            if product_id not in self._by_id:
                raise KeyError("product not found")
            product = self._by_id[product_id]
            return Product(**vars(product))

    def update_product(self, product_id: str, *, name: str | None, price: float | None) -> Product:
        with self._lock:
            if product_id not in self._by_id:
                raise KeyError("product not found")

            product = self._by_id[product_id]
            if name is not None:
                product.name = name
            if price is not None:
                product.price = price

            return Product(**vars(product))

    def delete_product(self, product_id: str) -> None:
        with self._lock:
            product = self.get_product(product_id)
            del self._by_id[product_id]
            del self._ids_by_sku[product.sku]
            self._stock_by_product_id.pop(product_id, None)

    def reset_state(self) -> None:
        """Clear in-memory state (test utility for deterministic runs)."""
        with self._lock:
            self._by_id.clear()
            self._ids_by_sku.clear()
            self._stock_by_product_id.clear()
            self._movements.clear()
            self._seq = 0
            self._movement_seq = 0


product_service = ProductService()
