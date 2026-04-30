from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.core.database import get_db
from app.models.models import Brand, User
from app.schemas.brand import Brand as BrandSchema, BrandCreate, BrandUpdate

router = APIRouter()

@router.get("/", response_model=List[BrandSchema])
async def read_brands(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve brands for the current tenant.
    """
    result = await db.execute(
        select(Brand)
        .where(Brand.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
    )
    brands = result.scalars().all()
    return brands

@router.post("/", response_model=BrandSchema)
async def create_brand(
    *,
    db: AsyncSession = Depends(get_db),
    brand_in: BrandCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new brand for the current tenant.
    """
    brand = Brand(
        **brand_in.dict(),
        tenant_id=current_user.tenant_id
    )
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand

@router.get("/{id}", response_model=BrandSchema)
async def read_brand(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get brand by ID.
    """
    result = await db.execute(
        select(Brand).where(Brand.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    brand = result.scalars().first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.put("/{id}", response_model=BrandSchema)
async def update_brand(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    brand_in: BrandUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a brand.
    """
    result = await db.execute(
        select(Brand).where(Brand.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    brand = result.scalars().first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    update_data = brand_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)
    
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand

@router.delete("/{id}", response_model=BrandSchema)
async def delete_brand(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a brand.
    """
    result = await db.execute(
        select(Brand).where(Brand.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    brand = result.scalars().first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    await db.delete(brand)
    await db.commit()
    return brand
