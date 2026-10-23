import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ShipmentItemCreate(BaseModel):
    order_item_id: uuid.UUID
    shipped_quantity: int = Field(..., gt=0)


class ShipmentItemResponse(ShipmentItemCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DeliveryEventCreate(BaseModel):
    event_status: str # DISPATCHED, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, EXCEPTION
    location: Optional[str] = None
    notes: Optional[str] = None


class DeliveryEventResponse(DeliveryEventCreate):
    id: uuid.UUID
    event_time: datetime
    model_config = ConfigDict(from_attributes=True)


class ShipmentBase(BaseModel):
    order_id: uuid.UUID
    carrier: str
    tracking_number: Optional[str] = None
    carton_count: int = 1
    shipping_cost: float = 0.00
    estimated_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class ShipmentCreate(ShipmentBase):
    items: List[ShipmentItemCreate]


class DispatchRequest(BaseModel):
    tracking_number: str
    dispatch_date: Optional[date] = None
    notes: Optional[str] = None


class MarkDeliveredRequest(BaseModel):
    actual_delivery_date: Optional[date] = None
    proof_of_delivery_url: Optional[str] = None
    notes: Optional[str] = None


class ShipmentResponse(ShipmentBase):
    id: uuid.UUID
    shipment_number: str
    dispatch_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    status: str
    proof_of_delivery_url: Optional[str] = None
    created_at: datetime
    items: List[ShipmentItemResponse] = []
    events: List[DeliveryEventResponse] = []
    model_config = ConfigDict(from_attributes=True)
