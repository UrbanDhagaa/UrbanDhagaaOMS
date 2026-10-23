import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.models.production import ProductionBatch
from app.schemas.production import (
    ProductionBatchCreate, ProductionBatchResponse, QualityCheckCreate, QualityCheckResponse
)
from app.dependencies import get_current_active_user
from app.services import production_service

router = APIRouter(prefix="/production", tags=["Production"])


@router.post("/batches", response_model=ProductionBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_in: ProductionBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await production_service.create_production_batch(
        db=db,
        batch_in=batch_in,
        actor_email=current_user.email
    )


@router.get("/batches", response_model=List[ProductionBatchResponse])
async def list_batches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(ProductionBatch).order_by(ProductionBatch.created_at.desc()))
    return list(res.scalars().all())


@router.post("/batches/{batch_id}/quality-checks", response_model=QualityCheckResponse, status_code=status.HTTP_201_CREATED)
async def record_qc(
    batch_id: uuid.UUID,
    qc_in: QualityCheckCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await production_service.record_quality_check(
        db=db,
        qc_in=qc_in,
        batch_id=batch_id,
        actor_email=current_user.email
    )
