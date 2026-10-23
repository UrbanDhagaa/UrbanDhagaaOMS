import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.production import ProductionBatch, QualityCheck
from app.models.orders import Order, OrderItem, OrderEvent
from app.schemas.production import ProductionBatchCreate, QualityCheckCreate, BatchProgressUpdate
from app.core.audit import record_audit_log


async def create_production_batch(
    db: AsyncSession,
    batch_in: ProductionBatchCreate,
    actor_email: str
) -> ProductionBatch:
    item_stmt = select(OrderItem).where(OrderItem.id == batch_in.order_item_id)
    item_res = await db.execute(item_stmt)
    order_item = item_res.scalar_one_or_none()
    if not order_item:
        raise HTTPException(status_code=404, detail="Order item not found")

    year = datetime.now(timezone.utc).year
    cnt_stmt = select(func.count(ProductionBatch.id))
    cnt = await db.execute(cnt_stmt)
    batch_num = f"BAT-{year}-{(cnt.scalar() or 0) + 1:04d}"

    batch = ProductionBatch(
        batch_number=batch_num,
        order_item_id=batch_in.order_item_id,
        assigned_vendor_id=batch_in.assigned_vendor_id,
        planned_quantity=batch_in.planned_quantity,
        completed_quantity=0,
        accepted_quantity=0,
        rejected_quantity=0,
        rework_quantity=0,
        status="IN_PROGRESS",
        start_date=batch_in.start_date,
        target_date=batch_in.target_date,
        notes=batch_in.notes
    )
    db.add(batch)

    # Update order production status
    ord_stmt = select(Order).where(Order.id == order_item.order_id)
    ord_res = await db.execute(ord_stmt)
    order = ord_res.scalar_one_or_none()
    if order and order.production_status == "Not Started":
        order.production_status = "In Progress"
        event = OrderEvent(
            order_id=order.id,
            event_type="PRODUCTION_STARTED",
            dimension="production",
            from_status="Not Started",
            to_status="In Progress",
            note=f"Production batch {batch_num} initiated",
            created_by=actor_email
        )
        db.add(event)

    await db.commit()
    await db.refresh(batch)
    return batch


async def record_quality_check(
    db: AsyncSession,
    qc_in: QualityCheckCreate,
    batch_id: uuid.UUID,
    actor_email: str
) -> QualityCheck:
    stmt = select(ProductionBatch).where(ProductionBatch.id == batch_id)
    res = await db.execute(stmt)
    batch = res.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Production batch not found")

    qc = QualityCheck(
        batch_id=batch.id,
        inspector_name=qc_in.inspector_name,
        inspected_quantity=qc_in.inspected_quantity,
        accepted_quantity=qc_in.accepted_quantity,
        rejected_quantity=qc_in.rejected_quantity,
        rework_quantity=qc_in.rework_quantity,
        inspection_date=qc_in.inspection_date,
        status=qc_in.status,
        defect_notes=qc_in.defect_notes
    )
    db.add(qc)

    batch.accepted_quantity += qc_in.accepted_quantity
    batch.rejected_quantity += qc_in.rejected_quantity
    batch.rework_quantity += qc_in.rework_quantity
    batch.completed_quantity += qc_in.inspected_quantity

    # Reconcile with OrderItem
    item_stmt = select(OrderItem).where(OrderItem.id == batch.order_item_id)
    item_res = await db.execute(item_stmt)
    order_item = item_res.scalar_one_or_none()
    if order_item:
        order_item.produced_quantity += qc_in.inspected_quantity
        order_item.accepted_qc_quantity += qc_in.accepted_quantity

        # Check if all items in the order have finished production
        ord_stmt = select(Order).where(Order.id == order_item.order_id)
        ord_res = await db.execute(ord_stmt)
        order = ord_res.scalar_one_or_none()
        if order:
            total_needed = sum(i.quantity for i in order.items)
            total_accepted = sum(i.accepted_qc_quantity for i in order.items)
            if total_accepted >= total_needed:
                order.production_status = "Completed"
                batch.status = "COMPLETED"

    await db.commit()
    await db.refresh(qc)
    return qc
