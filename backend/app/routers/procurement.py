import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.models.procurement import Vendor, PurchaseOrder
from app.schemas.procurement import (
    VendorCreate, VendorResponse, PurchaseOrderCreate, PurchaseOrderResponse,
    GoodsReceiptCreate, GoodsReceiptResponse
)
from app.dependencies import get_current_active_user
from app.services import procurement_service

router = APIRouter(prefix="/procurement", tags=["Procurement"])


@router.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor_in: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await procurement_service.create_vendor(
        db=db,
        vendor_in=vendor_in,
        actor_email=current_user.email
    )


@router.get("/vendors", response_model=List[VendorResponse])
async def list_vendors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await procurement_service.get_vendors(db)


@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await procurement_service.create_purchase_order(
        db=db,
        po_in=po_in,
        actor_email=current_user.email
    )


@router.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
async def list_purchase_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()))
    return list(res.scalars().all())


@router.post("/goods-receipts", response_model=GoodsReceiptResponse, status_code=status.HTTP_201_CREATED)
async def record_goods_receipt(
    gr_in: GoodsReceiptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await procurement_service.record_goods_receipt(
        db=db,
        gr_in=gr_in,
        actor_email=current_user.email
    )
