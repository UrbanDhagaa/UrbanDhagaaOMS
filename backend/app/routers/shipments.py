import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.models.fulfilment import Shipment
from app.schemas.fulfilment import (
    ShipmentCreate, ShipmentResponse, DispatchRequest, MarkDeliveredRequest
)
from app.dependencies import get_current_active_user
from app.services import fulfilment_service

router = APIRouter(prefix="/shipments", tags=["Fulfilment"])


@router.post("/", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_shipment(
    shipment_in: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await fulfilment_service.create_shipment(
        db=db,
        shipment_in=shipment_in,
        actor_email=current_user.email
    )


@router.get("/", response_model=List[ShipmentResponse])
async def list_shipments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(Shipment).order_by(Shipment.created_at.desc()))
    return list(res.scalars().all())


@router.post("/{shipment_id}/dispatch", response_model=ShipmentResponse)
async def dispatch(
    shipment_id: uuid.UUID,
    dispatch_in: DispatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await fulfilment_service.dispatch_shipment(
        db=db,
        shipment_id=shipment_id,
        dispatch_in=dispatch_in,
        actor_email=current_user.email
    )


@router.post("/{shipment_id}/delivered", response_model=ShipmentResponse)
async def mark_delivered(
    shipment_id: uuid.UUID,
    deliv_in: MarkDeliveredRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await fulfilment_service.mark_shipment_delivered(
        db=db,
        shipment_id=shipment_id,
        deliv_in=deliv_in,
        actor_email=current_user.email
    )
