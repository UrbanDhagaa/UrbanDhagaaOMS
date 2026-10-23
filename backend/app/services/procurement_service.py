import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.procurement import Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, ReceiptItem
from app.models.orders import Order, OrderEvent
from app.schemas.procurement import VendorCreate, PurchaseOrderCreate, GoodsReceiptCreate
from app.core.audit import record_audit_log


async def create_vendor(db: AsyncSession, vendor_in: VendorCreate, actor_email: str) -> Vendor:
    count_stmt = select(func.count(Vendor.id))
    cnt = await db.execute(count_stmt)
    code = f"VND-{(cnt.scalar() or 0) + 1:04d}"

    vendor = Vendor(
        vendor_code=code,
        name=vendor_in.name,
        contact_person=vendor_in.contact_person,
        email=vendor_in.email,
        phone=vendor_in.phone,
        gstin=vendor_in.gstin,
        address=vendor_in.address,
        capabilities=vendor_in.capabilities,
        status="ACTIVE"
    )
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor


async def get_vendors(db: AsyncSession) -> List[Vendor]:
    stmt = select(Vendor).order_by(Vendor.name.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def create_purchase_order(
    db: AsyncSession,
    po_in: PurchaseOrderCreate,
    actor_email: str
) -> PurchaseOrder:
    year = datetime.now(timezone.utc).year
    count_stmt = select(func.count(PurchaseOrder.id))
    cnt = await db.execute(count_stmt)
    po_num = f"PO-{year}-{(cnt.scalar() or 0) + 1:04d}"

    total_amount = sum(item.ordered_quantity * item.unit_cost for item in po_in.items)

    po = PurchaseOrder(
        po_number=po_num,
        vendor_id=po_in.vendor_id,
        order_id=po_in.order_id,
        status="ISSUED",
        expected_delivery_date=po_in.expected_delivery_date,
        total_amount=total_amount,
        notes=po_in.notes
    )
    db.add(po)
    await db.flush()

    for item_in in po_in.items:
        item = PurchaseOrderItem(
            po_id=po.id,
            order_item_id=item_in.order_item_id,
            item_description=item_in.item_description,
            ordered_quantity=item_in.ordered_quantity,
            received_quantity=0,
            unit_cost=item_in.unit_cost,
            total_cost=item_in.ordered_quantity * item_in.unit_cost
        )
        db.add(item)

    # If linked to customer order, update procurement status
    if po_in.order_id:
        ord_stmt = select(Order).where(Order.id == po_in.order_id)
        ord_res = await db.execute(ord_stmt)
        order = ord_res.scalar_one_or_none()
        if order:
            order.procurement_status = "Ordered"
            event = OrderEvent(
                order_id=order.id,
                event_type="PO_ISSUED",
                dimension="procurement",
                from_status="Not Ordered",
                to_status="Ordered",
                note=f"Purchase order {po_num} issued to supplier",
                created_by=actor_email
            )
            db.add(event)

    await db.commit()
    await db.refresh(po)
    return po


async def record_goods_receipt(
    db: AsyncSession,
    gr_in: GoodsReceiptCreate,
    actor_email: str
) -> GoodsReceipt:
    year = datetime.now(timezone.utc).year
    count_stmt = select(func.count(GoodsReceipt.id))
    cnt = await db.execute(count_stmt)
    gr_num = f"GRN-{year}-{(cnt.scalar() or 0) + 1:04d}"

    gr = GoodsReceipt(
        receipt_number=gr_num,
        po_id=gr_in.po_id,
        received_date=gr_in.received_date,
        received_by=gr_in.received_by or actor_email,
        notes=gr_in.notes
    )
    db.add(gr)
    await db.flush()

    for item_in in gr_in.items:
        item = ReceiptItem(
            receipt_id=gr.id,
            po_item_id=item_in.po_item_id,
            received_quantity=item_in.received_quantity,
            accepted_quantity=item_in.accepted_quantity,
            rejected_quantity=item_in.rejected_quantity,
            notes=item_in.notes
        )
        db.add(item)

        # Update PO Item received quantity
        poi_stmt = select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_in.po_item_id)
        poi_res = await db.execute(poi_stmt)
        poi = poi_res.scalar_one_or_none()
        if poi:
            poi.received_quantity += item_in.received_quantity

    await db.commit()
    await db.refresh(gr)
    return gr
