import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DesignApprovalBase(BaseModel):
    approver_name: str
    approver_role: str = "CLIENT"
    status: str # APPROVED, REJECTED
    comments: Optional[str] = None


class DesignApprovalCreate(DesignApprovalBase):
    pass


class DesignApprovalResponse(DesignApprovalBase):
    id: uuid.UUID
    asset_id: uuid.UUID
    approved_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DesignAssetBase(BaseModel):
    order_id: uuid.UUID
    order_item_id: Optional[uuid.UUID] = None
    file_name: str
    file_url: str
    file_type: str
    file_size: int = 0
    version: int = 1
    uploader: Optional[str] = None


class DesignAssetCreate(DesignAssetBase):
    pass


class DesignAssetResponse(DesignAssetBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    approvals: List[DesignApprovalResponse] = []
    model_config = ConfigDict(from_attributes=True)
