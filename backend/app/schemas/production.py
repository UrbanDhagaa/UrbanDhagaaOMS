import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QualityCheckBase(BaseModel):
    inspector_name: str
    inspected_quantity: int = Field(..., gt=0)
    accepted_quantity: int = Field(..., ge=0)
    rejected_quantity: int = 0
    rework_quantity: int = 0
    inspection_date: date
    status: str = "PASSED" # PASSED, FAILED, PARTIAL
    defect_notes: Optional[str] = None


class QualityCheckCreate(QualityCheckBase):
    pass


class QualityCheckResponse(QualityCheckBase):
    id: uuid.UUID
    batch_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductionBatchBase(BaseModel):
    order_item_id: uuid.UUID
    assigned_vendor_id: Optional[uuid.UUID] = None
    planned_quantity: int = Field(..., gt=0)
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    notes: Optional[str] = None


class ProductionBatchCreate(ProductionBatchBase):
    pass


class BatchProgressUpdate(BaseModel):
    completed_quantity: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ProductionBatchResponse(ProductionBatchBase):
    id: uuid.UUID
    batch_number: str
    completed_quantity: int
    accepted_quantity: int
    rejected_quantity: int
    rework_quantity: int
    status: str
    created_at: datetime
    quality_checks: List[QualityCheckResponse] = []
    model_config = ConfigDict(from_attributes=True)
