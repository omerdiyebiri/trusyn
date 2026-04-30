from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_db
from app.models.models import Incident, User, Brand
from app.schemas.incident import Incident as IncidentSchema, IncidentCreate
from app.tasks.scanner import analyze_incident
from app.tasks.reporter import send_abuse_reports

router = APIRouter()

@router.get("/", response_model=List[IncidentSchema])
async def read_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve incidents for the current tenant.
    """
    result = await db.execute(
        select(Incident)
        .join(Brand)
        .where(Brand.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
    )
    incidents = result.scalars().all()
    return incidents

@router.post("/", response_model=IncidentSchema)
async def create_incident(
    *,
    db: AsyncSession = Depends(get_db),
    incident_in: IncidentCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new incident (manual entry) and trigger analysis.
    """
    # Verify brand belongs to tenant
    result = await db.execute(
        select(Brand).where(Brand.id == incident_in.brand_id, Brand.tenant_id == current_user.tenant_id)
    )
    brand = result.scalars().first()
    if not brand:
        raise HTTPException(status_code=400, detail="Brand not found")

    incident = Incident(**incident_in.dict())
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    
    # Trigger async analysis
    analyze_incident.delay(str(incident.id))
    
    return incident

@router.post("/{id}/report")
async def trigger_report(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Manually trigger abuse reports for an incident.
    """
    result = await db.execute(
        select(Incident)
        .join(Brand)
        .where(Incident.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    send_abuse_reports.delay(str(incident.id))
    return {"message": "Report task triggered"}
