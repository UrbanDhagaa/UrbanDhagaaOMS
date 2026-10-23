import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ProductCategoryBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryResponse(ProductCategoryBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductVariantBase(BaseModel):
    sku: str
    size: Optional[str] = None
    colour: Optional[str] = None
    additional_attributes: Optional[Dict[str, Any]] = None
    price_override: Optional[float] = None
    is_active: bool = True


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantResponse(ProductVariantBase):
    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    sku: str
    name: str
    category_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    default_cost: float = 0.00
    default_price: float = 0.00
    attributes: Optional[Dict[str, Any]] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    variants: Optional[List[ProductVariantCreate]] = []


class ProductResponse(ProductBase):
    id: uuid.UUID
    created_at: datetime
    category: Optional[ProductCategoryResponse] = None
    variants: List[ProductVariantResponse] = []
    model_config = ConfigDict(from_attributes=True)
