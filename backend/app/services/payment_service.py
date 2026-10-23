import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.finance import Payment, PaymentAllocation, Invoice
from app.models.orders import Order, OrderEvent
from app.schemas.finance import PaymentCreate
from app.core.audit import record_audit_log


async def generate_receipt_number(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    count_stmt = select(func.count(Payment.id))
    result = await db.execute(count_stmt)
    total = result.scalar() or 0
    return f"RCPT-{year}-{(total + 1):04d}"


async def record_payment(
    db: AsyncSession,
    payment_in: PaymentCreate,
    actor_email: str
) -> Payment:
    receipt_num = await generate_receipt_number(db)

    payment = Payment(
        receipt_number=receipt_num,
        customer_id=payment_in.customer_id,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method,
        transaction_reference=payment_in.transaction_reference,
        received_date=payment_in.received_date,
        status="COMPLETED",
        notes=payment_in.notes,
        recorded_by=actor_email
    )
    db.add(payment)
    await db.flush()

    # Process allocations
    for alloc_in in payment_in.allocations or []:
        alloc = PaymentAllocation(
            payment_id=payment.id,
            invoice_id=alloc_in.invoice_id,
            order_id=alloc_in.order_id,
            allocated_amount=alloc_in.allocated_amount
        )
        db.add(alloc)

        # Update invoice if provided
        if alloc_in.invoice_id:
            inv_stmt = select(Invoice).where(Invoice.id == alloc_in.invoice_id)
            inv_res = await db.execute(inv_stmt)
            invoice = inv_res.scalar_one_or_none()
            if invoice:
                invoice.paid_amount += alloc_in.allocated_amount
                invoice.balance_due = max(0.0, float(invoice.total_amount) - invoice.paid_amount)
                if invoice.balance_due <= 0.01:
                    invoice.status = "PAID"
                else:
                    invoice.status = "PARTIALLY_PAID"

        # Update order if provided
        if alloc_in.order_id:
            ord_stmt = select(Order).where(Order.id == alloc_in.order_id)
            ord_res = await db.execute(ord_stmt)
            order = ord_res.scalar_one_or_none()
            if order:
                if order.order_status == "Cancelled":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot allocate payment to cancelled order {order.order_number}."
                    )
                # Calculate total allocated payments to this order
                tot_alloc_stmt = select(func.coalesce(func.sum(PaymentAllocation.allocated_amount), 0.0)).where(
                    PaymentAllocation.order_id == order.id
                )
                tot_res = await db.execute(tot_alloc_stmt)
                total_paid_so_far = float(tot_res.scalar() or 0.0) + alloc_in.allocated_amount

                old_status = order.payment_status
                if total_paid_so_far >= float(order.total_amount) - 0.01:
                    new_status = "Paid"
                elif total_paid_so_far > 0:
                    new_status = "Partially Paid"
                else:
                    new_status = "Unpaid"

                if old_status != new_status:
                    order.payment_status = new_status
                    event = OrderEvent(
                        order_id=order.id,
                        event_type="PAYMENT_RECEIVED",
                        dimension="payment",
                        from_status=old_status,
                        to_status=new_status,
                        note=f"Payment receipt {receipt_num} recorded for ₹{alloc_in.allocated_amount}",
                        created_by=actor_email
                    )
                    db.add(event)

    await record_audit_log(
        db=db,
        actor=actor_email,
        action="CREATE",
        entity_name="payments",
        entity_id=str(payment.id),
        after_state={"receipt_number": receipt_num, "amount": payment_in.amount},
        notes=f"Payment receipt {receipt_num} recorded."
    )

    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Payment], int]:
    stmt = select(Payment).order_by(Payment.created_at.desc())
    count_stmt = select(func.count(Payment.id))

    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    res = await db.execute(stmt.offset(skip).limit(limit))
    payments = res.scalars().all()
    return list(payments), total
