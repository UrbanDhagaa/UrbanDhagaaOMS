import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentAllocationBase(BaseModel):
    invoice_id: Optional[uuid.UUID] = None
    order_id: Optional[uuid.UUID] = None
    allocated_amount: float = Field(..., gt=0)


class PaymentAllocationCreate(PaymentAllocationBase):
    pass


class PaymentAllocationResponse(PaymentAllocationBase):
    id: uuid.UUID
    payment_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaymentBase(BaseModel):
    customer_id: uuid.UUID
    amount: float = Field(..., gt=0)
    payment_method: str = "NEFT" # NEFT, RTGS, UPI, CHEQUE, CARD, CASH
    transaction_reference: Optional[str] = None
    received_date: date
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    allocations: Optional[List[PaymentAllocationCreate]] = []


class PaymentResponse(PaymentBase):
    id: uuid.UUID
    receipt_number: str
    status: str
    recorded_by: Optional[str] = None
    created_at: datetime
    allocations: List[PaymentAllocationResponse] = []
    model_config = ConfigDict(from_attributes=True)


class InvoiceItemBase(BaseModel):
    order_item_id: Optional[uuid.UUID] = None
    item_name: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    tax_rate: float = 18.00


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    id: uuid.UUID
    total_price: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    order_id: uuid.UUID
    customer_id: uuid.UUID
    invoice_type: str = "TAX_INVOICE"
    invoice_date: date
    due_date: date
    gst_rate: float = 18.00


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]


class InvoiceResponse(InvoiceBase):
    id: uuid.UUID
    invoice_number: str
    status: str
    subtotal: float
    taxable_value: float
    gst_amount: float
    total_amount: float
    paid_amount: float
    balance_due: float
    created_at: datetime
    items: List[InvoiceItemResponse] = []
    model_config = ConfigDict(from_attributes=True)
