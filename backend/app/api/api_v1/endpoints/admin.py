from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core import security
from app.core.database import get_db
from app.models.models import Brand, Tenant, User, UserRole, VekaletStatus
from app.schemas.brand import Brand as BrandSchema
from app.schemas.tenant import Tenant as TenantSchema, TenantCreate
from app.schemas.user import User as UserSchema

router = APIRouter()


class VekaletReviewRequest(BaseModel):
    reason: Optional[str] = None


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.TENANT_STAFF

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


@router.get("/tenants/{tenant_id}/users", response_model=List[UserSchema])
async def list_tenant_users(
    *,
    db: AsyncSession = Depends(get_db),
    tenant_id: str,
    current_user: User = Depends(deps.get_current_super_admin),
) -> Any:
    """List users for a given tenant."""
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id)
    )
    return result.scalars().all()


@router.post("/tenants/{tenant_id}/users", response_model=UserSchema)
async def create_tenant_user(
    *,
    db: AsyncSession = Depends(get_db),
    tenant_id: str,
    body: AdminUserCreate,
    current_user: User = Depends(deps.get_current_super_admin),
) -> Any:
    """Create a new user under a specific tenant."""
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant_res.scalars().first():
        raise HTTPException(status_code=404, detail="Tenant not found")
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalars().first():
        raise HTTPException(status_code=400,
                            detail="A user with this email already exists")
    user = User(
        email=body.email,
        password_hash=security.get_password_hash(body.password),
        role=body.role,
        tenant_id=tenant_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/cloudflare/verify")
async def verify_cloudflare(
    *,
    current_user: User = Depends(deps.get_current_super_admin),
) -> Any:
    """Admin diagnostic — returns which configured CF auth method
    actually works against /user and /accounts/{id}. Use to debug
    submission failures without firing a real abuse report."""
    from app.services.cloudflare_abuse_service import verify_credentials
    return verify_credentials()


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
