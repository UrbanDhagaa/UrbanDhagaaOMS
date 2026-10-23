import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.schemas.finance import InvoiceCreate, InvoiceResponse
from app.schemas.common import PaginatedResponse
from app.dependencies import get_current_active_user, PaginationParams
from app.services import invoice_service

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def generate_invoice(
    inv_in: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await invoice_service.create_invoice(
        db=db,
        inv_in=inv_in,
        actor_email=current_user.email
    )


@router.get("/", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    items, total = await invoice_service.get_invoices(
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
