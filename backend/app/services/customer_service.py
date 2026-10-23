import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customers import Customer, CustomerContact, CustomerAddress
from app.models.finance import Payment
from app.models.orders import Order
from app.schemas.customers import CustomerCreate, CustomerUpdate
from app.core.audit import record_audit_log


async def generate_customer_code(db: AsyncSession) -> str:
    count_stmt = select(func.count(Customer.id))
    result = await db.execute(count_stmt)
    total = result.scalar() or 0
    return f"CUST-{(total + 1):04d}"


async def create_customer(
    db: AsyncSession,
    cust_in: CustomerCreate,
    actor_email: str
) -> Customer:
    # Check for duplicate by company name
    dup_stmt = select(Customer).where(func.lower(Customer.company_name) == cust_in.company_name.lower())
    dup_res = await db.execute(dup_stmt)
    if dup_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with company name '{cust_in.company_name}' already exists."
        )

    code = await generate_customer_code(db)

    customer = Customer(
        customer_code=code,
        company_name=cust_in.company_name,
        customer_type=cust_in.customer_type,
        gstin=cust_in.gstin,
        pan=cust_in.pan,
        website=cust_in.website,
        status="ACTIVE",
        payment_terms=cust_in.payment_terms,
        credit_limit=cust_in.credit_limit,
        notes=cust_in.notes,
    )
    db.add(customer)
    await db.flush()

    # Add contacts
    for contact_in in cust_in.contacts or []:
        contact = CustomerContact(
            customer_id=customer.id,
            name=contact_in.name,
            email=contact_in.email,
            phone=contact_in.phone,
            designation=contact_in.designation,
            is_primary=contact_in.is_primary,
        )
        db.add(contact)

    # Add addresses
    for addr_in in cust_in.addresses or []:
        address = CustomerAddress(
            customer_id=customer.id,
            address_type=addr_in.address_type,
            address_line1=addr_in.address_line1,
            address_line2=addr_in.address_line2,
            city=addr_in.city,
            state=addr_in.state,
            postal_code=addr_in.postal_code,
            country=addr_in.country,
            is_default=addr_in.is_default,
        )
        db.add(address)

    await record_audit_log(
        db=db,
        actor=actor_email,
        action="CREATE",
        entity_name="customers",
        entity_id=str(customer.id),
        after_state={"customer_code": code, "company_name": customer.company_name},
        notes=f"Customer {code} created."
    )

    await db.commit()
    await db.refresh(customer)
    return customer


async def get_customers(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None
) -> Tuple[List, int]:
    stmt = select(Customer)
    if search:
        f = f"%{search}%"
        stmt = stmt.where(
            or_(
                Customer.company_name.ilike(f),
                Customer.customer_code.ilike(f),
                Customer.gstin.ilike(f)
            )
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    stmt = stmt.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    customers = res.scalars().all()

    # Attach total_paid and payment_remaining for each customer
    result = []
    for c in customers:
        pay_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.customer_id == c.id,
            Payment.status == "COMPLETED"
        )
        pay_res = await db.execute(pay_stmt)
        total_paid = float(pay_res.scalar() or 0)

        # Sum total_amount of all non-cancelled orders for this customer
        ord_stmt = select(func.coalesce(func.sum(Order.total_amount), 0.0)).where(
            Order.customer_id == c.id,
            Order.order_status != "Cancelled"
        )
        ord_res = await db.execute(ord_stmt)
        total_ordered = float(ord_res.scalar() or 0.0)
        payment_remaining = max(0.0, total_ordered - total_paid)

        # Attach as attributes so Pydantic can read them
        c.__dict__['total_paid'] = total_paid
        c.__dict__['payment_remaining'] = payment_remaining
        result.append(c)

    return result, total


async def get_customer_by_id(db: AsyncSession, customer_id: uuid.UUID) -> Optional[Customer]:
    stmt = select(Customer).where(Customer.id == customer_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def update_customer(
    db: AsyncSession,
    customer_id: uuid.UUID,
    update_in: CustomerUpdate,
    actor_email: str
) -> Customer:
    stmt = select(Customer).where(Customer.id == customer_id)
    res = await db.execute(stmt)
    customer = res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = update_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)
    return customer
