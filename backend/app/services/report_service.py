from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.orders import Order
from app.models.finance import Payment, Invoice
from app.models.design import DesignAsset
from app.models.production import ProductionBatch
from app.models.fulfilment import Shipment
from app.schemas.reports import DashboardKPIs


async def get_dashboard_kpis(db: AsyncSession) -> DashboardKPIs:
    # Combine all 10 KPI metrics into 1 single round-trip query
    kpi_stmt = select(
        func.count(Order.id).label("total_orders"),
        func.coalesce(func.sum(case((Order.order_status.in_(["Draft", "Quoted", "Confirmed", "In Fulfilment", "Partially Dispatched"]), 1), else_=0)), 0).label("open_orders"),
        func.coalesce(func.sum(case((Order.order_status == "Confirmed", 1), else_=0)), 0).label("confirmed_orders"),
        func.coalesce(func.sum(case((Order.order_status == "In Fulfilment", 1), else_=0)), 0).label("in_fulfilment"),
        func.coalesce(func.sum(case((Order.order_status == "Delivered", 1), else_=0)), 0).label("delivered_orders"),
        func.coalesce(func.sum(case((Order.order_status != "Cancelled", Order.total_amount), else_=0.0)), 0.0).label("total_val"),
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(Payment.status == "COMPLETED").scalar_subquery().label("amt_rec"),
        select(func.count(DesignAsset.id)).where(DesignAsset.status.in_(["PENDING", "IN_REVIEW", "CHANGES_REQUIRED"])).scalar_subquery().label("pending_designs"),
        select(func.count(ProductionBatch.id)).where(ProductionBatch.status.in_(["IN_PROGRESS", "QUALITY_CHECK", "REWORK"])).scalar_subquery().label("batches_in_prod"),
        select(func.count(Shipment.id)).where(Shipment.status == "PENDING").scalar_subquery().label("pending_disp")
    )

    row = (await db.execute(kpi_stmt)).one()

    tot_orders = int(row.total_orders or 0)
    open_orders = int(row.open_orders or 0)
    confirmed_orders = int(row.confirmed_orders or 0)
    in_fulfilment = int(row.in_fulfilment or 0)
    delivered_orders = int(row.delivered_orders or 0)
    tot_val = float(row.total_val or 0.0)
    amt_rec = float(row.amt_rec or 0.0)
    outstanding = max(0.0, tot_val - amt_rec)
    pending_designs = int(row.pending_designs or 0)
    batches_in_prod = int(row.batches_in_prod or 0)
    pending_disp = int(row.pending_disp or 0)

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

