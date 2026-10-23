import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class VendorBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None


class VendorCreate(VendorBase):
    pass


class VendorResponse(VendorBase):
    id: uuid.UUID
    vendor_code: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderItemBase(BaseModel):
    order_item_id: Optional[uuid.UUID] = None
    item_description: str
    ordered_quantity: int = Field(..., gt=0)
    unit_cost: float = Field(..., ge=0)


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: uuid.UUID
    received_quantity: int
    total_cost: float
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    vendor_id: uuid.UUID
    order_id: Optional[uuid.UUID] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate]


class PurchaseOrderResponse(PurchaseOrderBase):
    id: uuid.UUID
    po_number: str
    status: str
    total_amount: float
    created_at: datetime
    vendor: Optional[VendorResponse] = None
    items: List[PurchaseOrderItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class ReceiptItemCreate(BaseModel):
    po_item_id: uuid.UUID
    received_quantity: int = Field(..., gt=0)
    accepted_quantity: int = Field(..., ge=0)
    rejected_quantity: int = 0
    notes: Optional[str] = None


class GoodsReceiptCreate(BaseModel):
    po_id: uuid.UUID
    received_date: date
    received_by: Optional[str] = None
    notes: Optional[str] = None
    items: List[ReceiptItemCreate]


class ReceiptItemResponse(ReceiptItemCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class GoodsReceiptResponse(BaseModel):
    id: uuid.UUID
    receipt_number: str
    po_id: uuid.UUID
    received_date: date
    received_by: Optional[str] = None
    notes: Optional[str] = None
    items: List[ReceiptItemResponse] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
