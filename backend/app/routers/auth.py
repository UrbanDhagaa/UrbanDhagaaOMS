from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User, Role
from app.schemas.identity import LoginRequest, Token, UserResponse, UserCreate
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(login_req: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == login_req.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/seed-admin")
async def seed_admin(db: AsyncSession = Depends(get_db)):
    """Convenience bootstrap endpoint to seed roles and default admin user."""
    roles_data = [
        ("ADMIN", "Manage users, configuration, overrides, and system administration"),
        ("SALES", "Manage customers, quotations, order drafts, and communications"),
        ("OPERATIONS", "Manage confirmed order execution, schedules, production, dispatch"),
        ("DESIGNER", "Access design jobs, upload revisions, record approvals"),
        ("PROCUREMENT", "Manage vendors, supplier POs, receipts, and supplier costs"),
        ("ACCOUNTS", "Manage payments, allocations, invoices, refunds, and receivables"),
        ("READ_ONLY", "View permitted records and reports"),
    ]

    for role_name, role_desc in roles_data:
        r_stmt = select(Role).where(Role.name == role_name)
        existing_role = (await db.execute(r_stmt)).scalar_one_or_none()
        if not existing_role:
            db.add(Role(name=role_name, description=role_desc))
    await db.flush()

    # Check if admin user exists
    admin_stmt = select(User).where(User.email == "admin@urbandhagaa.com")
    admin_user = (await db.execute(admin_stmt)).scalar_one_or_none()

    if not admin_user:
        admin_role_stmt = select(Role).where(Role.name == "ADMIN")
        admin_role = (await db.execute(admin_role_stmt)).scalar_one()

        admin_user = User(
            email="admin@urbandhagaa.com",
            hashed_password=get_password_hash("Admin@12345"),
            full_name="UrbanDhagaa Admin",
            phone="+91 9876543210",
            is_active=True,
            is_superuser=True,
            roles=[admin_role]
        )
        db.add(admin_user)
        await db.commit()
        return {"message": "Admin seeded successfully: admin@urbandhagaa.com / Admin@12345"}
    return {"message": "Admin already exists"}
