from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import asyncio

from app.api import deps
from app.core.database import get_db
from app.models.models import Incident, User, Brand
from app.schemas.incident import Incident as IncidentSchema, IncidentCreate, IncidentUpdate
from app.schemas.report import Report as ReportSchema
from app.models.models import Report
from app.tasks.scanner import analyze_incident, analyze_incident_async
from app.tasks.reporter import send_abuse_reports

router = APIRouter()

@router.get("/", response_model=List[IncidentSchema])
async def read_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
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
    
    asyncio.create_task(analyze_incident_async(str(incident.id)))
    
    return incident

@router.post("/{id}/report")
async def trigger_report(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Trigger abuse report sending for an incident.
    Determines applicable recipients (Cloudflare, hosting, registrar, Google DMCA)
    based on WHOIS/DNS evidence, then dispatches emails via Celery.
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

@router.post("/{id}/reanalyze")
async def reanalyze_incident(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Re-run evidence collection (Playwright + WHOIS + DNS) for an incident."""
    result = await db.execute(
        select(Incident)
        .join(Brand)
        .where(Incident.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    asyncio.create_task(analyze_incident_async(str(incident.id)))
    return {"message": "Re-analysis started in background"}


@router.post("/{id}/refetch-screenshot")
async def refetch_screenshot(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Run only the URLScan / PageSpeed fallback cascade against the
    incident's target URL and overwrite the stored screenshot. Useful
    when Playwright landed on a CF block page and the operator wants to
    try the external-network screenshot without re-running the whole
    evidence pipeline."""
    from app.services.screenshot_fallback_service import attempt_fallback
    result = await db.execute(
        select(Incident)
        .join(Brand)
        .where(Incident.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not incident.screenshot_path:
        raise HTTPException(status_code=400,
                            detail="Incident has no screenshot path to overwrite")

    target_url = incident.target_url
    screenshot_path = incident.screenshot_path
    incident_id = str(incident.id)

    async def _worker():
        from app.core.database import AsyncSessionLocal as ASL
        new_path = await attempt_fallback(target_url, screenshot_path)
        if new_path:
            async with ASL() as db2:
                row = (await db2.execute(
                    select(Incident).where(Incident.id == incident_id)
                )).scalars().first()
                if row:
                    row.screenshot_source = "fallback"
                    db2.add(row)
                    await db2.commit()

    asyncio.create_task(_worker())
    return {"message": "Fallback screenshot retry started"}

@router.get("/{id}/reports", response_model=List[ReportSchema])
async def list_incident_reports(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """List dispatched abuse reports for an incident, ordered by sent_at DESC."""
    result = await db.execute(
        select(Incident)
        .join(Brand)
        .where(Incident.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    reports = await db.execute(
        select(Report)
        .where(Report.incident_id == incident.id)
        .order_by(Report.sent_at.desc())
    )
    return reports.scalars().all()

@router.patch("/{id}", response_model=IncidentSchema)
async def update_incident(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    incident_in: IncidentUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an incident (e.g. mark as resolved, change status, override threat_type).
    """
    result = await db.execute(
        select(Incident)
        .join(Brand)
        .where(Incident.id == id, Brand.tenant_id == current_user.tenant_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_data = incident_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)

    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident
