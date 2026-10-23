import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.quotations import Quotation, QuotationItem
from app.models.orders import Order, OrderEvent
from app.models.customers import Customer
from app.schemas.quotations import QuotationCreate, QuotationAcceptRequest
from app.services.pricing_service import calculate_line_item, calculate_order_totals
from app.core.audit import record_audit_log


async def generate_quote_number(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    count_stmt = select(func.count(Quotation.id))
    result = await db.execute(count_stmt)
    total = result.scalar() or 0
    return f"QT-{year}-{(total + 1):04d}"


async def create_quotation(
    db: AsyncSession,
    quote_in: QuotationCreate,
    actor_email: str
) -> Quotation:
    quote_number = await generate_quote_number(db)

    # Compute totals
    items_raw = [
        {"quantity": item.quantity, "unit_price": item.unit_rate, "discount_amount": item.discount_amount}
        for item in quote_in.items
    ]
    totals = calculate_order_totals(
        items_raw,
        order_discount=quote_in.discount_amount,
        gst_rate=quote_in.gst_rate
    )

    quote = Quotation(
        quote_number=quote_number,
        version=1,
        order_id=quote_in.order_id,
        customer_id=quote_in.customer_id,
        status="DRAFT",
        valid_until=quote_in.valid_until,
        subtotal=float(totals["subtotal"]),
        discount_amount=float(totals["discount_amount"]),
        taxable_value=float(totals["taxable_value"]),
        gst_rate=float(totals["gst_rate"]),
        gst_amount=float(totals["gst_amount"]),
        total_amount=float(totals["total_amount"]),
        terms_and_conditions=quote_in.terms_and_conditions
    )
    db.add(quote)
    await db.flush()

    for item_in in quote_in.items:
        line = calculate_line_item(
            quantity=item_in.quantity,
            unit_price=item_in.unit_rate,
            discount_amount=item_in.discount_amount,
            tax_rate=item_in.tax_rate
        )
        q_item = QuotationItem(
            quotation_id=quote.id,
            item_name=item_in.item_name,
            specifications=item_in.specifications,
            quantity=item_in.quantity,
            unit_rate=item_in.unit_rate,
            discount_amount=item_in.discount_amount,
            tax_rate=item_in.tax_rate,
            tax_amount=float(line["tax_amount"]),
            total_amount=float(line["total_price"])
        )
        db.add(q_item)

    await record_audit_log(
        db=db,
        actor=actor_email,
        action="CREATE",
        entity_name="quotations",
        entity_id=str(quote.id),
        after_state={"quote_number": quote_number, "total_amount": float(totals["total_amount"])}
    )

    await db.commit()
    await db.refresh(quote)
    return quote


async def accept_quotation(
    db: AsyncSession,
    quotation_id: uuid.UUID,
    accept_in: QuotationAcceptRequest,
    actor_email: str
) -> Quotation:
    stmt = select(Quotation).where(Quotation.id == quotation_id)
    res = await db.execute(stmt)
    quote = res.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")

    quote.status = "ACCEPTED"

    # If linked to an order, confirm the order
    if quote.order_id and accept_in.auto_confirm_order:
        ord_stmt = select(Order).where(Order.id == quote.order_id)
        ord_res = await db.execute(ord_stmt)
        order = ord_res.scalar_one_or_none()
        if order and order.order_status == "Draft":
            order.order_status = "Confirmed"
            if accept_in.customer_po_reference:
                order.customer_po_reference = accept_in.customer_po_reference
            event = OrderEvent(
                order_id=order.id,
                event_type="ORDER_CONFIRMED",
                dimension="order",
                from_status="Draft",
                to_status="Confirmed",
                note=f"Confirmed automatically upon acceptance of Quotation {quote.quote_number}",
                created_by=actor_email
            )
            db.add(event)

    await record_audit_log(
        db=db,
        actor=actor_email,
        action="ACCEPT",
        entity_name="quotations",
        entity_id=str(quote.id),
        notes=f"Quotation {quote.quote_number} marked as ACCEPTED"
    )

    await db.commit()
    await db.refresh(quote)
    return quote
