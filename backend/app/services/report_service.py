from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.orders import Order
from app.models.finance import Payment, Invoice
from app.models.design import DesignAsset
from app.models.production import ProductionBatch
from app.models.fulfilment import Shipment
from app.schemas.reports import DashboardKPIs


async def get_dashboard_kpis(db: AsyncSession) -> DashboardKPIs:
    # Order counts
    total_orders_stmt = select(func.count(Order.id))
    tot_orders = (await db.execute(total_orders_stmt)).scalar() or 0

    open_orders_stmt = select(func.count(Order.id)).where(
        Order.order_status.in_(["Draft", "Quoted", "Confirmed", "In Fulfilment", "Partially Dispatched"])
    )
    open_orders = (await db.execute(open_orders_stmt)).scalar() or 0

    confirmed_stmt = select(func.count(Order.id)).where(Order.order_status == "Confirmed")
    confirmed_orders = (await db.execute(confirmed_stmt)).scalar() or 0

    fulfilment_stmt = select(func.count(Order.id)).where(Order.order_status == "In Fulfilment")
    in_fulfilment = (await db.execute(fulfilment_stmt)).scalar() or 0

    delivered_stmt = select(func.count(Order.id)).where(Order.order_status == "Delivered")
    delivered_orders = (await db.execute(delivered_stmt)).scalar() or 0

    # Financial sums
    total_val_stmt = select(func.coalesce(func.sum(Order.total_amount), 0.0)).where(
        Order.order_status != "Cancelled"
    )
    tot_val = float((await db.execute(total_val_stmt)).scalar() or 0.0)

    amount_rec_stmt = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
        Payment.status == "COMPLETED"
    )
    amt_rec = float((await db.execute(amount_rec_stmt)).scalar() or 0.0)

    outstanding = max(0.0, tot_val - amt_rec)

    # Operational metrics
    pending_designs_stmt = select(func.count(DesignAsset.id)).where(
        DesignAsset.status.in_(["PENDING", "IN_REVIEW", "CHANGES_REQUIRED"])
    )
    pending_designs = (await db.execute(pending_designs_stmt)).scalar() or 0

    production_batches_stmt = select(func.count(ProductionBatch.id)).where(
        ProductionBatch.status.in_(["IN_PROGRESS", "QUALITY_CHECK", "REWORK"])
    )
    batches_in_prod = (await db.execute(production_batches_stmt)).scalar() or 0

    pending_dispatches_stmt = select(func.count(Shipment.id)).where(
        Shipment.status == "PENDING"
    )
    pending_disp = (await db.execute(pending_dispatches_stmt)).scalar() or 0

    return DashboardKPIs(
        total_orders=tot_orders,
        open_orders=open_orders,
        confirmed_orders=confirmed_orders,
        in_fulfilment_orders=in_fulfilment,
        delivered_orders=delivered_orders,
        total_order_value=tot_val,
        amount_received=amt_rec,
        outstanding_receivables=outstanding,
        pending_design_approvals=pending_designs,
        batches_in_production=batches_in_prod,
        pending_dispatches=pending_disp,
    )
