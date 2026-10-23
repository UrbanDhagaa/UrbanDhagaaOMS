import uuid
from typing import List, Optional
from sqlalchemy import String, Numeric, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity


class ProductCategory(BaseEntity):
    __tablename__ = "product_categories"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")


class Product(BaseEntity):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    hsn_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    default_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    default_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped[Optional[ProductCategory]] = relationship("ProductCategory", back_populates="products", lazy="selectin")
    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan", lazy="selectin")


class ProductVariant(BaseEntity):
    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    colour: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    additional_attributes: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    price_override: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="variants")
