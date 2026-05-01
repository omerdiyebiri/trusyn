"""
Public, unauthenticated incident report pages.

Mirror of how Netcraft publishes https://incident.netcraft.com/reports/<id>/ —
abuse-desk recipients can click the link in our outbound mail and inspect the
evidence without needing a Trusyn account. The data exposed is intentionally
minimal: only the fields that already appear in the abuse mail body. Tenant
identifiers, user information, and unrelated incidents are NOT exposed.
"""

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import Incident
from app.services.abuse_service import confidence_band, defang


router = APIRouter()


def _resolve_storage_path(p: str) -> str:
    """Same logic abuse_service uses — accept absolute, anchor relative at /app."""
    if not p:
        return ""
    if os.path.isabs(p):
        return p
    return os.path.join("/app", p)


@router.get("/incidents/{id}")
async def public_incident(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Sanitized JSON for the public incident page."""
    result = await db.execute(
        select(Incident)
        .options(selectinload(Incident.brand))
        .where(Incident.id == id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    screenshot_resolved = _resolve_storage_path(incident.screenshot_path or "")
    has_screenshot = bool(
        incident.screenshot_path and os.path.exists(screenshot_resolved)
    )

    return {
        "id": str(incident.id),
        "target_url": incident.target_url,
        "defanged_url": defang(incident.target_url),
        "threat_type": (incident.threat_type.value
                        if incident.threat_type else None),
        "status": incident.status.value if incident.status else None,
        "confidence_band": confidence_band(incident.confidence_score),
        "confidence_score": incident.confidence_score,
        "discovered_at": (incident.discovered_at.isoformat()
                          if incident.discovered_at else None),
        "brand_name": incident.brand.name if incident.brand else None,
        "brand_official_url": (incident.brand.official_domains
                               if incident.brand else None),
        "has_screenshot": has_screenshot,
        "has_whois": bool(incident.whois_raw),
    }


@router.get("/incidents/{id}/screenshot")
async def public_screenshot(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Inline-serve the captured screenshot. PNG only."""
    result = await db.execute(
        select(Incident).where(Incident.id == id)
    )
    incident = result.scalars().first()
    if not incident or not incident.screenshot_path:
        raise HTTPException(status_code=404, detail="Screenshot not available")
    path = _resolve_storage_path(incident.screenshot_path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Screenshot file missing")
    return FileResponse(path, media_type="image/png")


@router.get("/incidents/{id}/whois", response_class=PlainTextResponse)
async def public_whois(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """Plain-text WHOIS / RDAP for the public report."""
    result = await db.execute(
        select(Incident).where(Incident.id == id)
    )
    incident = result.scalars().first()
    if not incident or not incident.whois_raw:
        raise HTTPException(status_code=404, detail="WHOIS not available")
    return PlainTextResponse(incident.whois_raw)
