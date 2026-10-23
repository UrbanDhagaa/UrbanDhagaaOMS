from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DashboardKPIs(BaseModel):
    total_orders: int = 0
    open_orders: int = 0
    confirmed_orders: int = 0
    in_fulfilment_orders: int = 0
    delivered_orders: int = 0
    total_order_value: float = 0.00
    amount_received: float = 0.00
    outstanding_receivables: float = 0.00
    pending_design_approvals: int = 0
    batches_in_production: int = 0
    pending_dispatches: int = 0


class OrderPipelineItem(BaseModel):
    status: str
    count: int
    total_value: float


class ReceivablesReportItem(BaseModel):
    customer_name: str
    order_number: str
    total_amount: float
    paid_amount: float
    balance_due: float
    days_overdue: int = 0
