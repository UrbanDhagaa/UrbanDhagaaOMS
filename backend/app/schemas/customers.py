import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerContactBase(BaseModel):
    name: str
    email: str
    phone: str
    designation: Optional[str] = None
    is_primary: bool = False


class CustomerContactCreate(CustomerContactBase):
    pass


class CustomerContactResponse(CustomerContactBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CustomerAddressBase(BaseModel):
    address_type: str = "SHIPPING"
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "India"
    is_default: bool = False


class CustomerAddressCreate(CustomerAddressBase):
    pass


class CustomerAddressResponse(CustomerAddressBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CustomerBase(BaseModel):
    company_name: str
    customer_type: str = "CORPORATE"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    website: Optional[str] = None
    payment_terms: str = "50_ADVANCE_50_DISPATCH"
    credit_limit: float = 0.00
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    contacts: Optional[List[CustomerContactCreate]] = []
    addresses: Optional[List[CustomerAddressCreate]] = []


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    customer_type: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = None
    notes: Optional[str] = None
    contact_number: Optional[str] = None
    whatsapp_link: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: uuid.UUID
    customer_code: str
    status: str
    contact_number: Optional[str] = None
    whatsapp_link: Optional[str] = None
    total_paid: Optional[float] = None
    payment_remaining: Optional[float] = None
    created_at: datetime
    contacts: List[CustomerContactResponse] = []
    addresses: List[CustomerAddressResponse] = []
    model_config = ConfigDict(from_attributes=True)
