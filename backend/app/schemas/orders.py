import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.customers import CustomerResponse


class OrderItemBase(BaseModel):
    product_id: Optional[uuid.UUID] = None
    variant_id: Optional[uuid.UUID] = None
    item_name: str
    specifications: Optional[Dict[str, Any]] = None
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    discount_amount: float = 0.00
    tax_rate: float = 18.00


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: uuid.UUID
    tax_amount: float
    total_price: float
    produced_quantity: int
    accepted_qc_quantity: int
    shipped_quantity: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OrderEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    dimension: str
    from_status: Optional[str] = None
    to_status: str
    note: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None
    category: str = "MER" # MER, GFT, WKT, MIX
    priority: str = "MEDIUM" # LOW, MEDIUM, HIGH, URGENT
    requested_delivery_date: Optional[date] = None
    committed_delivery_date: Optional[date] = None
    customer_po_reference: Optional[str] = None
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]
    discount_amount: float = 0.00
    gst_rate: float = 18.00


class OrderUpdate(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    requested_delivery_date: Optional[date] = None
    committed_delivery_date: Optional[date] = None
    customer_po_reference: Optional[str] = None
    notes: Optional[str] = None


class OrderStatusUpdateRequest(BaseModel):
    dimension: str = "order" # order, design, payment, procurement, production, delivery
    new_status: str
    note: Optional[str] = None


class OrderConfirmRequest(BaseModel):
    note: Optional[str] = "Customer accepted quotation and approved order."


class OrderCancelRequest(BaseModel):
    reason: str


class CustomerSummary(BaseModel):
    id: uuid.UUID
    customer_code: str
    company_name: str
    customer_type: str = "CORPORATE"
    gstin: Optional[str] = None
    payment_terms: str = "50_ADVANCE_50_DISPATCH"
    model_config = ConfigDict(from_attributes=True)


class OrderResponse(OrderBase):
    id: uuid.UUID
    order_number: str

    order_status: str
    design_status: str
    payment_status: str
    procurement_status: str
    production_status: str
    delivery_status: str

    subtotal: float
    discount_amount: float
    taxable_value: float
    gst_rate: float
    gst_amount: float
    total_amount: float
    paid_amount: float = 0.00
    payment_remaining: float = 0.00

    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    customer: Optional[CustomerSummary] = None
    items: List[OrderItemResponse] = []
    events: List[OrderEventResponse] = []

    model_config = ConfigDict(from_attributes=True)
