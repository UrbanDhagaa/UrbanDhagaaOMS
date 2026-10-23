from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.schemas.reports import DashboardKPIs
from app.dependencies import get_current_active_user
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard-kpis", response_model=DashboardKPIs)
async def get_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await report_service.get_dashboard_kpis(db)
