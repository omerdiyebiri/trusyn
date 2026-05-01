from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.core.database import get_db
from app.models.models import Tenant, User
from app.schemas.tenant import Tenant as TenantSchema, TenantCreate

router = APIRouter()

@router.get("/tenants", response_model=List[TenantSchema])
async def read_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_super_admin),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all tenants (Super Admin only).
    """
    result = await db.execute(select(Tenant).offset(skip).limit(limit))
    tenants = result.scalars().all()
    return tenants

@router.post("/tenants", response_model=TenantSchema)
async def create_tenant(
    *,
    db: AsyncSession = Depends(get_db),
    tenant_in: TenantCreate,
    current_user: User = Depends(deps.get_current_super_admin),
) -> Any:
    """
    Create a new tenant (Super Admin only).
    """
    tenant = Tenant(**tenant_in.dict())
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant
