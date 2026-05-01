from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_db
from app.models.models import Brand, Tenant, User, VekaletStatus
from app.schemas.brand import Brand as BrandSchema
from app.schemas.tenant import Tenant as TenantSchema, TenantCreate

router = APIRouter()


class VekaletReviewRequest(BaseModel):
    reason: Optional[str] = None

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


@router.get("/vekalet/pending", response_model=List[BrandSchema])
async def list_pending_vekalet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_super_admin),
) -> Any:
    """List brands awaiting vekalet review."""
    result = await db.execute(
        select(Brand).where(Brand.vekalet_status == VekaletStatus.PENDING.value)
    )
    return result.scalars().all()


@router.post("/brands/{id}/vekalet/approve", response_model=BrandSchema)
async def approve_vekalet(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_super_admin),
) -> Any:
    result = await db.execute(select(Brand).where(Brand.id == id))
    brand = result.scalars().first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    if not brand.vekalet_pdf_path:
        raise HTTPException(status_code=400, detail="No vekalet uploaded")
    brand.vekalet_status = VekaletStatus.APPROVED.value
    brand.vekalet_reviewed_at = datetime.utcnow()
    brand.vekalet_reject_reason = None
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


@router.post("/brands/{id}/vekalet/reject", response_model=BrandSchema)
async def reject_vekalet(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    body: VekaletReviewRequest,
    current_user: User = Depends(deps.get_current_super_admin),
) -> Any:
    result = await db.execute(select(Brand).where(Brand.id == id))
    brand = result.scalars().first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    brand.vekalet_status = VekaletStatus.REJECTED.value
    brand.vekalet_reviewed_at = datetime.utcnow()
    brand.vekalet_reject_reason = body.reason or "Document did not meet requirements"
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


@router.get("/brands/{id}/vekalet/file")
async def download_vekalet(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_super_admin),
):
    """Admin-only download of the uploaded vekalet PDF for review."""
    from fastapi.responses import FileResponse
    import os
    result = await db.execute(select(Brand).where(Brand.id == id))
    brand = result.scalars().first()
    if not brand or not brand.vekalet_pdf_path:
        raise HTTPException(status_code=404, detail="Vekalet not found")
    if not os.path.exists(brand.vekalet_pdf_path):
        raise HTTPException(status_code=404, detail="Vekalet file missing on disk")
    return FileResponse(brand.vekalet_pdf_path, media_type="application/pdf",
                        filename=f"vekalet_{brand.id}.pdf")
