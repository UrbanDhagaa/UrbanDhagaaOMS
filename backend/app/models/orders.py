import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    String, Integer, Numeric, ForeignKey, JSON, Date, DateTime, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity, Base, TimestampMixin, utc_now


class OrderCounter(Base):
    __tablename__ = "order_counters"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Order(BaseEntity):
    __tablename__ = "orders"

    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(20), default="MER", nullable=False) # MER, GFT, WKT, MIX
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, URGENT

    # Multi-dimensional statuses
    order_status: Mapped[str] = mapped_column(String(50), default="Draft", index=True, nullable=False)
    design_status: Mapped[str] = mapped_column(String(50), default="Not Required", index=True, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(50), default="Unpaid", index=True, nullable=False)
    procurement_status: Mapped[str] = mapped_column(String(50), default="Not Required", index=True, nullable=False)
    production_status: Mapped[str] = mapped_column(String(50), default="Not Started", index=True, nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(50), default="Not Dispatched", index=True, nullable=False)

    requested_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    committed_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    customer_po_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Snapshot commercial figures
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    taxable_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.00, nullable=False)
    gst_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)

    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders", lazy="selectin")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    events: Mapped[List["OrderEvent"]] = relationship("OrderEvent", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    quotations: Mapped[List["Quotation"]] = relationship("Quotation", back_populates="order")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="order")
    design_assets: Mapped[List["DesignAsset"]] = relationship("DesignAsset", back_populates="order")
    shipments: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="order")


class OrderItem(BaseEntity):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )

    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    specifications: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.00, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    # Tracking reconciliation quantities
    produced_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_qc_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shipped_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product", lazy="selectin")
    variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant", lazy="selectin")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_item_qty_positive"),
    )


class OrderEvent(BaseEntity):
    __tablename__ = "order_events"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    dimension: Mapped[str] = mapped_column(String(50), default="order", nullable=False) # order, design, payment, etc.
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    order: Mapped[Order] = relationship("Order", back_populates="events")
