import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseEntity, utc_now


class DesignAsset(BaseEntity):
    __tablename__ = "design_assets"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. pdf, ai, png
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    uploader: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False) # PENDING, IN_REVIEW, CHANGES_REQUIRED, APPROVED

    order: Mapped["Order"] = relationship("Order", back_populates="design_assets")
    approvals: Mapped[List["DesignApproval"]] = relationship(
        "DesignApproval", back_populates="asset", cascade="all, delete-orphan", lazy="selectin"
    )


class DesignApproval(BaseEntity):
    __tablename__ = "design_approvals"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("design_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approver_name: Mapped[str] = mapped_column(String(150), nullable=False)
    approver_role: Mapped[str] = mapped_column(String(50), default="CLIENT", nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # APPROVED, REJECTED
    comments: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    asset: Mapped[DesignAsset] = relationship("DesignAsset", back_populates="approvals")
