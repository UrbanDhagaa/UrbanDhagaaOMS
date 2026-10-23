import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.design import DesignAsset, DesignApproval
from app.models.orders import Order, OrderEvent
from app.schemas.design import DesignAssetCreate, DesignApprovalCreate
from app.core.audit import record_audit_log


async def create_design_asset(
    db: AsyncSession,
    asset_in: DesignAssetCreate,
    actor_email: str
) -> DesignAsset:
    ord_stmt = select(Order).where(Order.id == asset_in.order_id)
    ord_res = await db.execute(ord_stmt)
    order = ord_res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    asset = DesignAsset(
        order_id=asset_in.order_id,
        order_item_id=asset_in.order_item_id,
        file_name=asset_in.file_name,
        file_url=asset_in.file_url,
        file_type=asset_in.file_type,
        file_size=asset_in.file_size,
        version=asset_in.version,
        uploader=actor_email,
        status="IN_REVIEW"
    )
    db.add(asset)

    # Update order design_status if not approved
    if order.design_status != "Approved":
        order.design_status = "In Review"

    await db.commit()
    await db.refresh(asset)
    return asset


async def record_design_approval(
    db: AsyncSession,
    asset_id: uuid.UUID,
    approval_in: DesignApprovalCreate,
    actor_email: str
) -> DesignApproval:
    stmt = select(DesignAsset).where(DesignAsset.id == asset_id)
    res = await db.execute(stmt)
    asset = res.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Design asset not found")

    approval = DesignApproval(
        asset_id=asset.id,
        approver_name=approval_in.approver_name,
        approver_role=approval_in.approver_role,
        status=approval_in.status,
        comments=approval_in.comments
    )
    db.add(approval)

    asset.status = "APPROVED" if approval_in.status == "APPROVED" else "CHANGES_REQUIRED"

    # Check if all assets for the order are approved
    ord_stmt = select(Order).where(Order.id == asset.order_id)
    ord_res = await db.execute(ord_stmt)
    order = ord_res.scalar_one_or_none()
    if order:
        if approval_in.status == "APPROVED":
            order.design_status = "Approved"
            event = OrderEvent(
                order_id=order.id,
                event_type="DESIGN_APPROVED",
                dimension="design",
                from_status="In Review",
                to_status="Approved",
                note=f"Artwork approved by {approval_in.approver_name}",
                created_by=actor_email
            )
            db.add(event)
        else:
            order.design_status = "Changes Required"

    await db.commit()
    await db.refresh(approval)
    return approval
