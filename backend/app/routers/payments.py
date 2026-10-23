import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.schemas.finance import PaymentCreate, PaymentResponse
from app.schemas.common import PaginatedResponse
from app.dependencies import get_current_active_user, PaginationParams
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_new_payment(
    payment_in: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await payment_service.record_payment(
        db=db,
        payment_in=payment_in,
        actor_email=current_user.email
    )


@router.get("/", response_model=PaginatedResponse[PaymentResponse])
async def list_payments(
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    items, total = await payment_service.get_payments(
        db=db,
        skip=params.offset,
        limit=params.page_size
    )
    total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages
    }
