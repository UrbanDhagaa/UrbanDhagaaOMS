import uuid
from datetime import date
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity


class Payment(BaseEntity):
    __tablename__ = "payments"

    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="NEFT", nullable=False) # NEFT, RTGS, UPI, CHEQUE, CARD, CASH
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False) # COMPLETED, FAILED, REFUNDED
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    recorded_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    allocations: Mapped[List["PaymentAllocation"]] = relationship(
        "PaymentAllocation", back_populates="payment", cascade="all, delete-orphan", lazy="selectin"
    )


class PaymentAllocation(BaseEntity):
    __tablename__ = "payment_allocations"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    allocated_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    payment: Mapped[Payment] = relationship("Payment", back_populates="allocations")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="allocations")


class Invoice(BaseEntity):
    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    invoice_type: Mapped[str] = mapped_column(String(50), default="TAX_INVOICE", nullable=False) # TAX_INVOICE, PROFORMA
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ISSUED", nullable=False) # DRAFT, ISSUED, PARTIALLY_PAID, PAID, CANCELLED

    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    taxable_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.00, nullable=False)
    gst_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    balance_due: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="invoices")
    items: Mapped[List["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin"
    )
    allocations: Mapped[List[PaymentAllocation]] = relationship(
        "PaymentAllocation", back_populates="invoice"
    )


class InvoiceItem(BaseEntity):
    __tablename__ = "invoice_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True
    )

    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.00, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="items")
