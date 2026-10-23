import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, ForeignKey, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity, utc_now


class Shipment(BaseEntity):
    __tablename__ = "shipments"

    shipment_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    carrier: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. BlueDart, Delhivery, DTDC, Porter
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    carton_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)

    dispatch_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    estimated_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False) # PENDING, DISPATCHED, IN_TRANSIT, DELIVERED, EXCEPTION
    proof_of_delivery_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="shipments")
    items: Mapped[List["ShipmentItem"]] = relationship(
        "ShipmentItem", back_populates="shipment", cascade="all, delete-orphan", lazy="selectin"
    )
    events: Mapped[List["DeliveryEvent"]] = relationship(
        "DeliveryEvent", back_populates="shipment", cascade="all, delete-orphan", lazy="selectin"
    )


class ShipmentItem(BaseEntity):
    __tablename__ = "shipment_items"

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    shipped_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    shipment: Mapped[Shipment] = relationship("Shipment", back_populates="items")
    order_item: Mapped["OrderItem"] = relationship("OrderItem", lazy="selectin")


class DeliveryEvent(BaseEntity):
    __tablename__ = "delivery_events"

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_status: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    shipment: Mapped[Shipment] = relationship("Shipment", back_populates="events")
