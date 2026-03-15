"""Products API router with role-based access control and audit traces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.audit import record_audit_event
from app.core.auth import AuthContext
from app.core.permissions import require_roles
from app.modules.products.schemas import (
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from app.modules.products.service import Product, product_service

router = APIRouter(prefix="/products", tags=["products"])


def _to_response(product: Product) -> ProductResponse:
    return ProductResponse(id=product.id, sku=product.sku, name=product.name, price=product.price)


@router.get("", response_model=ProductListResponse)
def list_products(_: AuthContext = Depends(require_roles("admin", "bodega", "cajero"))) -> ProductListResponse:
    products = [_to_response(item) for item in product_service.list_products()]
    return ProductListResponse(items=products)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreateRequest,
    auth: AuthContext = Depends(require_roles("admin", "bodega")),
) -> ProductResponse:
    try:
        created = product_service.create_product(sku=payload.sku, name=payload.name, price=payload.price)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="products.create",
        entity=created.id,
        metadata={"sku": created.sku},
    )
    return _to_response(created)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    _: AuthContext = Depends(require_roles("admin", "bodega", "cajero")),
) -> ProductResponse:
    try:
        product = product_service.get_product(product_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _to_response(product)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    auth: AuthContext = Depends(require_roles("admin", "bodega")),
) -> ProductResponse:
    try:
        updated = product_service.update_product(product_id, name=payload.name, price=payload.price)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="products.update",
        entity=updated.id,
        metadata={"name": updated.name, "price": updated.price},
    )
    return _to_response(updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_product(
    product_id: str,
    auth: AuthContext = Depends(require_roles("admin")),
) -> Response:
    try:
        product_service.delete_product(product_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(
        actor_id=auth.subject,
        action="products.delete",
        entity=product_id,
        metadata={},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
