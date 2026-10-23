import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.models.quotations import Quotation
from app.schemas.quotations import QuotationCreate, QuotationResponse, QuotationAcceptRequest
from app.dependencies import get_current_active_user
from app.services import quotation_service

router = APIRouter(prefix="/quotations", tags=["Quotations"])


@router.post("/", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_in: QuotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await quotation_service.create_quotation(
        db=db,
        quote_in=quote_in,
        actor_email=current_user.email
    )


@router.get("/", response_model=List[QuotationResponse])
async def list_quotes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(Quotation).order_by(Quotation.created_at.desc()))
    return list(res.scalars().all())


@router.post("/{quotation_id}/accept", response_model=QuotationResponse)
async def accept_quote(
    quotation_id: uuid.UUID,
    accept_in: QuotationAcceptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await quotation_service.accept_quotation(
        db=db,
        quotation_id=quotation_id,
        accept_in=accept_in,
        actor_email=current_user.email
    )
