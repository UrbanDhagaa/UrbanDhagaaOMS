import uuid
from typing import List, Optional
from sqlalchemy import String, Numeric, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity


class Customer(BaseEntity):
    __tablename__ = "customers"

    customer_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    customer_type: Mapped[str] = mapped_column(String(50), default="CORPORATE", nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    whatsapp_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    payment_terms: Mapped[str] = mapped_column(String(100), default="50_ADVANCE_50_DISPATCH", nullable=False)
    credit_limit: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    contacts: Mapped[List["CustomerContact"]] = relationship(
        "CustomerContact", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    addresses: Mapped[List["CustomerAddress"]] = relationship(
        "CustomerAddress", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")


class CustomerContact(BaseEntity):
    __tablename__ = "customer_contacts"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(25), nullable=False)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="contacts")


class CustomerAddress(BaseEntity):
    __tablename__ = "customer_addresses"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_type: Mapped[str] = mapped_column(String(20), default="SHIPPING", nullable=False) # BILLING, SHIPPING
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="addresses")
