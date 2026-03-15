"""In-memory service layer for products module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass
class Product:
    id: str
    sku: str
    name: str
    price: float


class ProductService:
    """Application service encapsulating product CRUD rules."""

    def __init__(self) -> None:
        self._by_id: dict[str, Product] = {}
        self._ids_by_sku: dict[str, str] = {}
        self._seq = 0
        self._lock = Lock()

    def list_products(self) -> list[Product]:
        return list(self._by_id.values())

    def create_product(self, *, sku: str, name: str, price: float) -> Product:
        with self._lock:
            if sku in self._ids_by_sku:
                raise ValueError("sku already exists")

            self._seq += 1
            product_id = f"prod-{self._seq:04d}"
            product = Product(id=product_id, sku=sku, name=name, price=price)
            self._by_id[product_id] = product
            self._ids_by_sku[sku] = product_id
            return product

    def get_product(self, product_id: str) -> Product:
        if product_id not in self._by_id:
            raise KeyError("product not found")
        return self._by_id[product_id]

    def update_product(self, product_id: str, *, name: str | None, price: float | None) -> Product:
        product = self.get_product(product_id)

        if name is not None:
            product.name = name
        if price is not None:
            product.price = price

        return product

    def delete_product(self, product_id: str) -> None:
        with self._lock:
            product = self.get_product(product_id)
            del self._by_id[product_id]
            del self._ids_by_sku[product.sku]


product_service = ProductService()
