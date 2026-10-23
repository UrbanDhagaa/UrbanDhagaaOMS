import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.fulfilment import Shipment, ShipmentItem, DeliveryEvent
from app.models.orders import Order, OrderItem, OrderEvent
from app.schemas.fulfilment import ShipmentCreate, DispatchRequest, MarkDeliveredRequest, DeliveryEventCreate
from app.core.audit import record_audit_log


async def create_shipment(
    db: AsyncSession,
    shipment_in: ShipmentCreate,
    actor_email: str
) -> Shipment:
    ord_stmt = select(Order).where(Order.id == shipment_in.order_id)
    ord_res = await db.execute(ord_stmt)
    order = ord_res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    year = datetime.now(timezone.utc).year
    cnt_stmt = select(func.count(Shipment.id))
    cnt = await db.execute(cnt_stmt)
    shipment_num = f"SHP-{year}-{(cnt.scalar() or 0) + 1:04d}"

    shipment = Shipment(
        shipment_number=shipment_num,
        order_id=shipment_in.order_id,
        carrier=shipment_in.carrier,
        tracking_number=shipment_in.tracking_number,
        carton_count=shipment_in.carton_count,
        shipping_cost=shipment_in.shipping_cost,
        estimated_delivery_date=shipment_in.estimated_delivery_date,
        status="PENDING",
        notes=shipment_in.notes
    )
    db.add(shipment)
    await db.flush()

    for item_in in shipment_in.items:
        # Validate that shipped quantity does not exceed ordered quantity
        item_stmt = select(OrderItem).where(OrderItem.id == item_in.order_item_id)
        item_res = await db.execute(item_stmt)
        order_item = item_res.scalar_one_or_none()
        if not order_item:
            raise HTTPException(status_code=404, detail=f"Order item {item_in.order_item_id} not found")

        remaining_to_ship = order_item.quantity - order_item.shipped_quantity
        if item_in.shipped_quantity > remaining_to_ship:
            raise HTTPException(
                status_code=400,
                detail=f"Shipped quantity {item_in.shipped_quantity} exceeds remaining undelivered quantity ({remaining_to_ship}) for item '{order_item.item_name}'"
            )

        shp_item = ShipmentItem(
            shipment_id=shipment.id,
            order_item_id=item_in.order_item_id,
            shipped_quantity=item_in.shipped_quantity
        )
        db.add(shp_item)
        order_item.shipped_quantity += item_in.shipped_quantity

    await db.commit()
    await db.refresh(shipment)
    return shipment


async def dispatch_shipment(
    db: AsyncSession,
    shipment_id: uuid.UUID,
    dispatch_in: DispatchRequest,
    actor_email: str
) -> Shipment:
    stmt = select(Shipment).where(Shipment.id == shipment_id)
    res = await db.execute(stmt)
    shipment = res.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment.status = "DISPATCHED"
    shipment.tracking_number = dispatch_in.tracking_number
    shipment.dispatch_date = dispatch_in.dispatch_date or datetime.now(timezone.utc).date()

    event = DeliveryEvent(
        shipment_id=shipment.id,
        event_status="DISPATCHED",
        location="UrbanDhagaa Warehouse",
        notes=f"Dispatched via {shipment.carrier} tracking #{dispatch_in.tracking_number}"
    )
    db.add(event)

    # Reconcile Order delivery status
    ord_stmt = select(Order).where(Order.id == shipment.order_id)
    ord_res = await db.execute(ord_stmt)
    order = ord_res.scalar_one_or_none()
    if order:
        total_qty = sum(i.quantity for i in order.items)
        total_shipped = sum(i.shipped_quantity for i in order.items)

        old_status = order.delivery_status
        new_status = "In Transit" if total_shipped >= total_qty else "Partially Dispatched"
        order.delivery_status = new_status
        if order.order_status in ["Draft", "Confirmed"]:
            order.order_status = "In Fulfilment"

        ord_event = OrderEvent(
            order_id=order.id,
            event_type="ORDER_DISPATCHED",
            dimension="delivery",
            from_status=old_status,
            to_status=new_status,
            note=f"Shipment {shipment.shipment_number} dispatched",
            created_by=actor_email
        )
        db.add(ord_event)

    await db.commit()
    await db.refresh(shipment)
    return shipment


async def mark_shipment_delivered(
    db: AsyncSession,
    shipment_id: uuid.UUID,
    deliv_in: MarkDeliveredRequest,
    actor_email: str
) -> Shipment:
    stmt = select(Shipment).where(Shipment.id == shipment_id)
    res = await db.execute(stmt)
    shipment = res.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment.status = "DELIVERED"
    shipment.actual_delivery_date = deliv_in.actual_delivery_date or datetime.now(timezone.utc).date()
    if deliv_in.proof_of_delivery_url:
        shipment.proof_of_delivery_url = deliv_in.proof_of_delivery_url

    event = DeliveryEvent(
        shipment_id=shipment.id,
        event_status="DELIVERED",
        notes=deliv_in.notes or "Package safely delivered to customer."
    )
    db.add(event)

    ord_stmt = select(Order).where(Order.id == shipment.order_id)
    ord_res = await db.execute(ord_stmt)
    order = ord_res.scalar_one_or_none()
    if order:
        total_qty = sum(i.quantity for i in order.items)
        total_shipped = sum(i.shipped_quantity for i in order.items)
        if total_shipped >= total_qty:
            order.delivery_status = "Delivered"
            if order.order_status != "Closed":
                order.order_status = "Delivered"

    await db.commit()
    await db.refresh(shipment)
    return shipment
