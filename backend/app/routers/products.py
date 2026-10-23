import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.identity import User
from app.models.catalogue import Product, ProductCategory, ProductVariant
from app.schemas.catalogue import (
    ProductCreate, ProductResponse, ProductCategoryCreate, ProductCategoryResponse
)
from app.dependencies import get_current_active_user, PaginationParams

router = APIRouter(prefix="/products", tags=["Catalogue"])


@router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    cat_in: ProductCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    cat = ProductCategory(code=cat_in.code, name=cat_in.name, description=cat_in.description)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.get("/categories", response_model=List[ProductCategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(ProductCategory).order_by(ProductCategory.name.asc()))
    return list(res.scalars().all())


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    prod_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    prod = Product(
        sku=prod_in.sku,
        name=prod_in.name,
        category_id=prod_in.category_id,
        description=prod_in.description,
        hsn_code=prod_in.hsn_code,
        default_cost=prod_in.default_cost,
        default_price=prod_in.default_price,
        attributes=prod_in.attributes or {},
        is_active=prod_in.is_active
    )
    db.add(prod)
    await db.flush()

    for v in prod_in.variants or []:
        variant = ProductVariant(
            product_id=prod.id,
            sku=v.sku,
            size=v.size,
            colour=v.colour,
            additional_attributes=v.additional_attributes or {},
            price_override=v.price_override,
            is_active=v.is_active
        )
        db.add(variant)

    await db.commit()
    await db.refresh(prod)
    return prod


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(Product).order_by(Product.name.asc()))
    return list(res.scalars().all())
