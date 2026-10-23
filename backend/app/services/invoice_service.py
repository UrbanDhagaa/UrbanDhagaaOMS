import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.finance import Invoice, InvoiceItem
from app.models.orders import Order
from app.schemas.finance import InvoiceCreate
from app.core.audit import record_audit_log


async def generate_invoice_number(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    count_stmt = select(func.count(Invoice.id))
    result = await db.execute(count_stmt)
    total = result.scalar() or 0
    return f"INV-{year}-{(total + 1):04d}"


async def create_invoice(
    db: AsyncSession,
    inv_in: InvoiceCreate,
    actor_email: str
) -> Invoice:
    inv_num = await generate_invoice_number(db)

    subtotal = sum(item.quantity * item.unit_price for item in inv_in.items)
    gst_amount = round(subtotal * (inv_in.gst_rate / 100.0), 2)
    total_amount = round(subtotal + gst_amount, 2)

    invoice = Invoice(
        invoice_number=inv_num,
        order_id=inv_in.order_id,
        customer_id=inv_in.customer_id,
        invoice_type=inv_in.invoice_type,
        invoice_date=inv_in.invoice_date,
        due_date=inv_in.due_date,
        status="ISSUED",
        subtotal=subtotal,
        taxable_value=subtotal,
        gst_rate=inv_in.gst_rate,
        gst_amount=gst_amount,
        total_amount=total_amount,
        paid_amount=0.00,
        balance_due=total_amount
    )
    db.add(invoice)
    await db.flush()

    for item_in in inv_in.items:
        line_total = round(item_in.quantity * item_in.unit_price * (1 + item_in.tax_rate / 100.0), 2)
        inv_item = InvoiceItem(
            invoice_id=invoice.id,
            order_item_id=item_in.order_item_id,
            item_name=item_in.item_name,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            tax_rate=item_in.tax_rate,
            total_price=line_total
        )
        db.add(inv_item)

    await record_audit_log(
        db=db,
        actor=actor_email,
        action="CREATE",
        entity_name="invoices",
        entity_id=str(invoice.id),
        after_state={"invoice_number": inv_num, "total_amount": total_amount}
    )

    await db.commit()
    await db.refresh(invoice)
    return invoice


async def get_invoices(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Invoice], int]:
    stmt = select(Invoice).order_by(Invoice.created_at.desc())
    count_stmt = select(func.count(Invoice.id))
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    res = await db.execute(stmt.offset(skip).limit(limit))
    invoices = res.scalars().all()
    return list(invoices), total
