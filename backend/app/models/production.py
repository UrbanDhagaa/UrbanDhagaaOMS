import uuid
from datetime import date
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity


class ProductionBatch(BaseEntity):
    __tablename__ = "production_batches"

    batch_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True
    )
    planned_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rework_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="NOT_STARTED", nullable=False) # NOT_STARTED, IN_PROGRESS, QUALITY_CHECK, REWORK, COMPLETED
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    quality_checks: Mapped[List["QualityCheck"]] = relationship(
        "QualityCheck", back_populates="batch", cascade="all, delete-orphan", lazy="selectin"
    )


class QualityCheck(BaseEntity):
    __tablename__ = "quality_checks"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("production_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inspector_name: Mapped[str] = mapped_column(String(100), nullable=False)
    inspected_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    rejected_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rework_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PASSED", nullable=False) # PASSED, FAILED, PARTIAL
    defect_notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    batch: Mapped[ProductionBatch] = relationship("ProductionBatch", back_populates="quality_checks")
