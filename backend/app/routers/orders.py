import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.schemas.orders import (
    OrderCreate, OrderResponse, OrderConfirmRequest, OrderCancelRequest, OrderStatusUpdateRequest
)
from app.schemas.common import PaginatedResponse
from app.dependencies import get_current_active_user, PaginationParams
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_new_order(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await order_service.create_order(
        db=db,
        order_in=order_in,
        actor_email=current_user.email
    )


@router.get("/", response_model=PaginatedResponse[OrderResponse])
async def list_orders(
    params: PaginationParams = Depends(),
    order_status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    delivery_status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    items, total = await order_service.get_orders(
        db=db,
        skip=params.offset,
        limit=params.page_size,
        search=params.search,
        order_status=order_status,
        payment_status=payment_status,
        delivery_status=delivery_status,
        category=category
    )
    total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_existing_order(
    order_id: uuid.UUID,
    confirm_in: OrderConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await order_service.confirm_order(
        db=db,
        order_id=order_id,
        actor_email=current_user.email,
        note=confirm_in.note
    )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_existing_order(
    order_id: uuid.UUID,
    cancel_in: OrderCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await order_service.cancel_order(
        db=db,
        order_id=order_id,
        reason=cancel_in.reason,
        actor_email=current_user.email
    )


@router.post("/{order_id}/status", response_model=OrderResponse)
async def update_dimension_status(
    order_id: uuid.UUID,
    req: OrderStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await order_service.update_order_status(
        db=db,
        order_id=order_id,
        req=req,
        actor_email=current_user.email
    )
