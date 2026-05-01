import os
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.core.database import get_db
from app.models.models import Brand, User, VekaletStatus
from app.schemas.brand import Brand as BrandSchema, BrandCreate, BrandUpdate

from app.services.report_service import report_service
from fastapi.responses import FileResponse

router = APIRouter()

VEKALET_STORAGE = os.path.abspath("/app/storage/vekalet")
VEKALET_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
os.makedirs(VEKALET_STORAGE, exist_ok=True)

@router.get("/{id}/report")
async def generate_brand_pdf_report(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate and download a PDF security report for a brand.
    """
    result = await db.execute(
        select(Brand).where(Brand.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    brand = result.scalars().first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Fetch incidents for this brand
    from app.models.models import Incident
    inc_result = await db.execute(
        select(Incident).where(Incident.brand_id == brand.id)
    )
    incidents = inc_result.scalars().all()
    
    # Convert models to dicts for the service
    incident_data = [
        {
            "target_url": i.target_url,
            "threat_type": i.threat_type,
            "status": i.status,
            "confidence_score": i.confidence_score
        } for i in incidents
    ]
    
    pdf_path = report_service.generate_brand_report(brand.name, incident_data)
    
    return FileResponse(
        path=pdf_path,
        filename=os.path.basename(pdf_path),
        media_type='application/pdf'
    )

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

@router.post("/{id}/vekalet", response_model=BrandSchema)
async def upload_vekalet(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Upload power-of-attorney PDF for the brand. Sets status to PENDING for admin review."""
    result = await db.execute(
        select(Brand).where(Brand.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    brand = result.scalars().first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    payload = await file.read()
    if len(payload) > VEKALET_MAX_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5 MB limit")
    if not payload.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")

    filename = f"{brand.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join(VEKALET_STORAGE, filename)
    with open(path, "wb") as f:
        f.write(payload)

    brand.vekalet_pdf_path = path
    brand.vekalet_status = VekaletStatus.PENDING.value
    brand.vekalet_uploaded_at = datetime.utcnow()
    brand.vekalet_reviewed_at = None
    brand.vekalet_reject_reason = None
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
