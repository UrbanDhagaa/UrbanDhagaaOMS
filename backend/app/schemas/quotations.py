import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class QuotationItemBase(BaseModel):
    item_name: str
    specifications: Optional[Dict[str, Any]] = None
    quantity: int = Field(..., gt=0)
    unit_rate: float = Field(..., ge=0)
    discount_amount: float = 0.00
    tax_rate: float = 18.00


class QuotationItemCreate(QuotationItemBase):
    pass


class QuotationItemResponse(QuotationItemBase):
    id: uuid.UUID
    tax_amount: float
    total_amount: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class QuotationBase(BaseModel):
    customer_id: uuid.UUID
    order_id: Optional[uuid.UUID] = None
    valid_until: Optional[date] = None
    discount_amount: float = 0.00
    gst_rate: float = 18.00
    terms_and_conditions: Optional[str] = None


class QuotationCreate(QuotationBase):
    items: List[QuotationItemCreate]


class QuotationAcceptRequest(BaseModel):
    auto_confirm_order: bool = True
    customer_po_reference: Optional[str] = None


class QuotationResponse(QuotationBase):
    id: uuid.UUID
    quote_number: str
    version: int
    status: str
    subtotal: float
    taxable_value: float
    gst_amount: float
    total_amount: float
    created_at: datetime
    items: List[QuotationItemResponse] = []
    model_config = ConfigDict(from_attributes=True)
