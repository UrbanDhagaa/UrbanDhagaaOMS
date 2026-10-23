import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.models.design import DesignAsset
from app.schemas.design import DesignAssetCreate, DesignAssetResponse, DesignApprovalCreate, DesignApprovalResponse
from app.dependencies import get_current_active_user
from app.services import design_service

router = APIRouter(prefix="/design", tags=["Design"])


@router.post("/assets", response_model=DesignAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset_metadata(
    asset_in: DesignAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await design_service.create_design_asset(
        db=db,
        asset_in=asset_in,
        actor_email=current_user.email
    )


@router.post("/assets/{asset_id}/approve", response_model=DesignApprovalResponse)
async def record_approval(
    asset_id: uuid.UUID,
    approval_in: DesignApprovalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await design_service.record_design_approval(
        db=db,
        asset_id=asset_id,
        approval_in=approval_in,
        actor_email=current_user.email
    )


@router.get("/assets", response_model=List[DesignAssetResponse])
async def list_design_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(DesignAsset).order_by(DesignAsset.created_at.desc()))
    return list(res.scalars().all())
