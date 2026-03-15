"""Schemas for product CRUD endpoints."""

from pydantic import BaseModel, Field


class ProductCreateRequest(BaseModel):
    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    price: float = Field(gt=0)


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    price: float | None = Field(default=None, gt=0)


class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    price: float


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
