import uuid
from datetime import date
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, ForeignKey, JSON, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity


class Vendor(BaseEntity):
    __tablename__ = "vendors"

    vendor_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)

    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="vendor")


class PurchaseOrder(BaseEntity):
    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False) # DRAFT, ISSUED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    vendor: Mapped[Vendor] = relationship("Vendor", back_populates="purchase_orders", lazy="selectin")
    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan", lazy="selectin"
    )
    receipts: Mapped[List["GoodsReceipt"]] = relationship("GoodsReceipt", back_populates="purchase_order")


class PurchaseOrderItem(BaseEntity):
    __tablename__ = "purchase_order_items"

    po_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True
    )
    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    ordered_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="items")


class GoodsReceipt(BaseEntity):
    __tablename__ = "goods_receipts"

    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    po_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="receipts")
    items: Mapped[List["ReceiptItem"]] = relationship(
        "ReceiptItem", back_populates="receipt", cascade="all, delete-orphan", lazy="selectin"
    )


class ReceiptItem(BaseEntity):
    __tablename__ = "receipt_items"

    receipt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    po_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_order_items.id", ondelete="RESTRICT"), nullable=False
    )
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    receipt: Mapped[GoodsReceipt] = relationship("GoodsReceipt", back_populates="items")
