import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.orders import Order, OrderCounter, OrderItem, OrderEvent
from app.models.finance import PaymentAllocation
from app.models.customers import Customer
from app.schemas.orders import OrderCreate, OrderUpdate, OrderStatusUpdateRequest
from app.services.pricing_service import calculate_line_item, calculate_order_totals
from app.core.audit import record_audit_log
from app.core.outbox import emit_outbox_event


async def generate_next_order_number(db: AsyncSession) -> str:
    current_year = datetime.now(timezone.utc).year

    # Row-lock the counter row for the current year
    stmt = select(OrderCounter).where(OrderCounter.year == current_year).with_for_update()
    result = await db.execute(stmt)
    counter = result.scalar_one_or_none()

    if not counter:
        counter = OrderCounter(year=current_year, current_value=1)
        db.add(counter)
        await db.flush()
        next_seq = 1
    else:
        counter.current_value += 1
        await db.flush()
        next_seq = counter.current_value

    return f"UD-{current_year}-{next_seq:05d}"


async def create_order(
    db: AsyncSession,
    order_in: OrderCreate,
    actor_email: str
) -> Order:
    # 1. Resolve Customer (by ID or manual Company Name)
    customer = None
    if order_in.customer_id:
        cust_stmt = select(Customer).where(Customer.id == order_in.customer_id)
        cust_res = await db.execute(cust_stmt)
        customer = cust_res.scalar_one_or_none()

    if not customer and order_in.company_name and order_in.company_name.strip():
        clean_name = order_in.company_name.strip()
        name_stmt = select(Customer).where(func.lower(Customer.company_name) == clean_name.lower())
        name_res = await db.execute(name_stmt)
        customer = name_res.scalar_one_or_none()

        if not customer:
            count_stmt = select(func.count(Customer.id))
            cnt = (await db.execute(count_stmt)).scalar() or 0
            new_code = f"CUST-{(cnt + 1):04d}"
            customer = Customer(
                customer_code=new_code,
                company_name=clean_name,
                customer_type="CORPORATE",
                status="ACTIVE",
                payment_terms="50_ADVANCE_50_DISPATCH",
                credit_limit=0.00
            )
            db.add(customer)
            await db.flush()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid Customer or enter a Company Name."
        )

    # 2. Generate canonical Order ID atomically
    order_number = await generate_next_order_number(db)

    # 3. Compute Item and Order Totals
    items_raw = [item.model_dump() for item in order_in.items]
    totals = calculate_order_totals(
        items_raw,
        order_discount=order_in.discount_amount,
        gst_rate=order_in.gst_rate
    )

    # 4. Create Order Header
    order = Order(
        order_number=order_number,
        customer_id=customer.id,
        category=order_in.category,
        priority=order_in.priority,
        order_status="Draft",
        design_status="Not Required",
        payment_status="Unpaid",
        procurement_status="Not Required",
        production_status="Not Started",
        delivery_status="Not Dispatched",
        requested_delivery_date=order_in.requested_delivery_date,
        committed_delivery_date=order_in.committed_delivery_date,
        customer_po_reference=order_in.customer_po_reference,
        subtotal=float(totals["subtotal"]),
        discount_amount=float(totals["discount_amount"]),
        taxable_value=float(totals["taxable_value"]),
        gst_rate=float(totals["gst_rate"]),
        gst_amount=float(totals["gst_amount"]),
        total_amount=float(totals["total_amount"]),
        notes=order_in.notes,
    )
    db.add(order)
    await db.flush()

    # 5. Create Order Items
    for item_in in order_in.items:
        line_calc = calculate_line_item(
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            discount_amount=item_in.discount_amount,
            tax_rate=item_in.tax_rate
        )
        item = OrderItem(
            order_id=order.id,
            product_id=item_in.product_id,
            variant_id=item_in.variant_id,
            item_name=item_in.item_name,
            specifications=item_in.specifications,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            discount_amount=item_in.discount_amount,
            tax_rate=item_in.tax_rate,
            tax_amount=float(line_calc["tax_amount"]),
            total_price=float(line_calc["total_price"]),
        )
        db.add(item)

    # 6. Record Initial Order Event
    event = OrderEvent(
        order_id=order.id,
        event_type="ORDER_CREATED",
        dimension="order",
        from_status=None,
        to_status="Draft",
        note=f"Order {order_number} created in Draft status.",
        created_by=actor_email
    )
    db.add(event)

    # 7. Record Audit Log
    await record_audit_log(
        db=db,
        actor=actor_email,
        action="CREATE",
        entity_name="orders",
        entity_id=str(order.id),
        after_state={"order_number": order_number, "total_amount": float(totals["total_amount"])},
        notes=f"Created order {order_number}"
    )

    # 8. Emit Outbox Event
    await emit_outbox_event(
        db=db,
        event_type="ORDER_CREATED",
        payload={"order_id": str(order.id), "order_number": order_number, "customer_id": str(customer.id)}
    )

    await db.commit()
    await db.refresh(order)
    return order


async def get_orders(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    order_status: Optional[str] = None,
    payment_status: Optional[str] = None,
    delivery_status: Optional[str] = None,
    category: Optional[str] = None
) -> Tuple[List[Order], int]:
    stmt = select(Order)

    if order_status:
        stmt = stmt.where(Order.order_status == order_status)
    if payment_status:
        stmt = stmt.where(Order.payment_status == payment_status)
    if delivery_status:
        stmt = stmt.where(Order.delivery_status == delivery_status)
    if category:
        stmt = stmt.where(Order.category == category)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.join(Order.customer).where(
            or_(
                Order.order_number.ilike(search_filter),
                Customer.company_name.ilike(search_filter),
                Order.customer_po_reference.ilike(search_filter)
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Paginate and order by newest
    stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    orders = res.scalars().all()

    # Attach paid_amount and payment_remaining per order
    result = []
    for order in orders:
        paid_stmt = select(func.coalesce(func.sum(PaymentAllocation.allocated_amount), 0.0)).where(
            PaymentAllocation.order_id == order.id
        )
        paid_res = await db.execute(paid_stmt)
        paid = float(paid_res.scalar() or 0.0)
        if order.payment_status == "Paid" and paid == 0:
            paid = float(order.total_amount)
        if order.order_status == "Cancelled":
            remaining = 0.0
        else:
            remaining = max(0.0, float(order.total_amount) - paid)
        order.__dict__['paid_amount'] = paid
        order.__dict__['payment_remaining'] = remaining
        result.append(order)

    return result, total


async def get_order_by_id(db: AsyncSession, order_id: uuid.UUID) -> Optional[Order]:
    stmt = select(Order).where(Order.id == order_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def confirm_order(
    db: AsyncSession,
    order_id: uuid.UUID,
    actor_email: str,
    note: Optional[str] = None
) -> Order:
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.order_status in ["Cancelled", "Closed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm order in {order.order_status} state."
        )

    if not order.items:
        raise HTTPException(
            status_code=400,
            detail="Cannot confirm an order with no line items."
        )

    old_status = order.order_status
    order.order_status = "Confirmed"

    event = OrderEvent(
        order_id=order.id,
        event_type="ORDER_CONFIRMED",
        dimension="order",
        from_status=old_status,
        to_status="Confirmed",
        note=note or "Order confirmed for production and fulfilment.",
        created_by=actor_email
    )
    db.add(event)

    await record_audit_log(
        db=db,
        actor=actor_email,
        action="CONFIRM",
        entity_name="orders",
        entity_id=str(order.id),
        before_state={"order_status": old_status},
        after_state={"order_status": "Confirmed"},
        notes=note
    )

    await db.commit()
    await db.refresh(order)
    return order


async def update_order_status(
    db: AsyncSession,
    order_id: uuid.UUID,
    req: OrderStatusUpdateRequest,
    actor_email: str
) -> Order:
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    valid_dimensions = [
        "order", "design", "payment", "procurement", "production", "delivery"
    ]
    if req.dimension not in valid_dimensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dimension {req.dimension}. Valid: {valid_dimensions}"
        )

    if order.order_status == "Cancelled":
        if req.dimension == "payment":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment status and amount cannot be modified because the order is cancelled."
            )
        if req.dimension == "order" and req.new_status != "Cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change status of a cancelled order."
            )

    attr_name = f"{req.dimension}_status" if req.dimension != "order" else "order_status"
    old_status = getattr(order, attr_name)

    setattr(order, attr_name, req.new_status)

    event = OrderEvent(
        order_id=order.id,
        event_type=f"{req.dimension.upper()}_STATUS_CHANGED",
        dimension=req.dimension,
        from_status=old_status,
        to_status=req.new_status,
        note=req.note,
        created_by=actor_email
    )
    db.add(event)

    await record_audit_log(
        db=db,
        actor=actor_email,
        action="STATUS_CHANGE",
        entity_name="orders",
        entity_id=str(order.id),
        before_state={attr_name: old_status},
        after_state={attr_name: req.new_status},
        notes=req.note
    )

    await db.commit()
    await db.refresh(order)
    return order


async def cancel_order(
    db: AsyncSession,
    order_id: uuid.UUID,
    reason: str,
    actor_email: str
) -> Order:
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.delivery_status in ["Delivered"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel an order that has already been delivered."
        )

    old_status = order.order_status
    order.order_status = "Cancelled"
    order.cancellation_reason = reason

    event = OrderEvent(
        order_id=order.id,
        event_type="ORDER_CANCELLED",
        dimension="order",
        from_status=old_status,
        to_status="Cancelled",
        note=f"Cancellation reason: {reason}",
        created_by=actor_email
    )
    db.add(event)

    await record_audit_log(
        db=db,
        actor=actor_email,
        action="CANCEL",
        entity_name="orders",
        entity_id=str(order.id),
        before_state={"order_status": old_status},
        after_state={"order_status": "Cancelled", "reason": reason},
        notes=reason
    )

    await db.commit()
    await db.refresh(order)
    return order
