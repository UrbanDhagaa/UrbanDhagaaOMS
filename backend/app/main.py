from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, AsyncSessionLocal
from app.models.base import Base
# Import all models to ensure they are registered with Base metadata
import app.models  # noqa
from app.routers import (
    auth, customers, products, orders, quotations, payments,
    invoices, design, procurement, production, shipments, reports
)
from app.routers.auth import seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables are created
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Automatically bootstrap default admin & roles if first launch
    async with AsyncSessionLocal() as session:
        try:
            await seed_admin(session)
        except Exception as e:
            print(f"Notice: initial admin seed step: {e}")

    yield

    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="UrbanDhagaa Order Management System API - Corporate Merchandise and Gifting",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    origins = [origins]
has_wildcard = "*" in origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if has_wildcard else origins,
    allow_origin_regex=r"https://.*\.vercel\.app" if not has_wildcard else None,
    allow_credentials=not has_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include all modular routers under /api/v1
api_prefix = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api_prefix)
app.include_router(customers.router, prefix=api_prefix)
app.include_router(products.router, prefix=api_prefix)
app.include_router(orders.router, prefix=api_prefix)
app.include_router(quotations.router, prefix=api_prefix)
app.include_router(payments.router, prefix=api_prefix)
app.include_router(invoices.router, prefix=api_prefix)
app.include_router(design.router, prefix=api_prefix)
app.include_router(procurement.router, prefix=api_prefix)
app.include_router(production.router, prefix=api_prefix)
app.include_router(shipments.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)


@app.get("/api/v1/health", tags=["Health"])
async def healthcheck():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "database": "configured"
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to UrbanDhagaa Order Management System API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
