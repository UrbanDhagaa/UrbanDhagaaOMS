import uuid
from datetime import date
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, ForeignKey, JSON, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity


class Quotation(BaseEntity):
    __tablename__ = "quotations"

    quote_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False) # DRAFT, SENT, ACCEPTED, REJECTED, EXPIRED, SUPERSEDED
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    taxable_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.00, nullable=False)
    gst_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)

    terms_and_conditions: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    order: Mapped[Optional["Order"]] = relationship("Order", back_populates="quotations")
    items: Mapped[List["QuotationItem"]] = relationship(
        "QuotationItem", back_populates="quotation", cascade="all, delete-orphan", lazy="selectin"
    )


class QuotationItem(BaseEntity):
    __tablename__ = "quotation_items"

    quotation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    specifications: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_rate: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.00, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    quotation: Mapped[Quotation] = relationship("Quotation", back_populates="items")
