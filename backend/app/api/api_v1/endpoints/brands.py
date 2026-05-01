from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.core.database import get_db
from app.models.models import Brand, User
from app.schemas.brand import Brand as BrandSchema, BrandCreate, BrandUpdate

from app.services.report_service import report_service
from fastapi.responses import FileResponse

router = APIRouter()
...
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
