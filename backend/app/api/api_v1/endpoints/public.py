"""
Public, unauthenticated incident report pages.

Mirror of how Netcraft publishes https://incident.netcraft.com/reports/<id>/ —
abuse-desk recipients can click the link in our outbound mail and inspect the
evidence without needing a Trusyn account. The data exposed is intentionally
minimal: only the fields that already appear in the abuse mail body. Tenant
identifiers, user information, and unrelated incidents are NOT exposed.
"""

import logging
import os
import time
from collections import deque
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from datetime import datetime, timezone
from typing import Any, Optional

import aiosmtplib
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.models import Incident
from app.services.abuse_service import confidence_band, defang


router = APIRouter()
logger = logging.getLogger(__name__)


# ---- naive in-process rate limiter for public form posts ------------------
# We don't want a single visitor flooding takedowns@trusyn.io. Window is
# rolling 15 minutes, capped per source IP. Process-local — fine until we
# need horizontal scale; revisit with Redis when we do.
_RATE_LIMIT_WINDOW_S = 15 * 60
_RATE_LIMIT_MAX_HITS = 5
_rate_buckets: dict = {}


def _rate_limit_check(source_ip: str) -> None:
    now = time.time()
    bucket = _rate_buckets.setdefault(source_ip, deque())
    cutoff = now - _RATE_LIMIT_WINDOW_S
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= _RATE_LIMIT_MAX_HITS:
        raise HTTPException(status_code=429,
                            detail="Too many submissions. Try again later.")
    bucket.append(now)


async def _send_internal_mail(subject: str, body: str,
                              reply_to: Optional[str] = None) -> None:
    """Forward a public form submission to the takedowns inbox.
    Silently logs and returns on missing config — landing form should
    not 500 if SMTP is misconfigured in dev."""
    if not settings.SMTP_HOST or not settings.SMTP_PASSWORD:
        logger.warning("Public form submission discarded — SMTP not configured")
        return
    msg = EmailMessage()
    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    msg["To"] = settings.EMAILS_FROM_EMAIL
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(timezone.utc))
    msg["Message-ID"] = make_msgid(domain="trusyn.io")
    msg["Auto-Submitted"] = "auto-generated"
    msg["X-Trusyn-Source"] = "public-form"
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_TLS,
        )
    except Exception as exc:
        logger.error("Public form mail send failed: %s", exc)


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


@router.get("/incidents/{id}/vekalet")
async def public_vekalet(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Power-of-attorney PDF for the brand referenced by this incident.

    Exposed so registrars / hosts that receive the abuse mail can verify
    that Trusyn is acting on behalf of an authorized brand owner before
    taking action. The PDF is served only when the brand vekalet has been
    admin-approved (status == APPROVED) — otherwise we return 404 to keep
    the URL pattern stable while reports are blocked anyway.
    """
    from fastapi.responses import FileResponse
    from app.models.models import VekaletStatus
    result = await db.execute(
        select(Incident).options(selectinload(Incident.brand)).where(Incident.id == id)
    )
    incident = result.scalars().first()
    if not incident or not incident.brand:
        raise HTTPException(status_code=404, detail="Incident not found")
    brand = incident.brand
    if brand.vekalet_status != VekaletStatus.APPROVED.value:
        raise HTTPException(status_code=404, detail="Power of attorney not available")
    if not brand.vekalet_pdf_path or not os.path.exists(brand.vekalet_pdf_path):
        raise HTTPException(status_code=404, detail="Power of attorney file missing")
    return FileResponse(
        brand.vekalet_pdf_path, media_type="application/pdf",
        filename=f"trusyn-poa-{brand.name.replace(' ', '_')}.pdf",
    )


# ===========================================================================
# Public form submissions (contact + spam/phishing report)
# ===========================================================================


class ContactSubmission(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    organization: Optional[str] = Field(None, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


class SpamReportSubmission(BaseModel):
    suspicious_url: str = Field(..., min_length=4, max_length=2048)
    impersonated_brand: Optional[str] = Field(None, max_length=200)
    reporter_email: Optional[EmailStr] = None
    notes: Optional[str] = Field(None, max_length=5000)


def _client_ip(request: Request) -> str:
    """Trust the proxy chain — Coolify / Cloudflare set X-Forwarded-For."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/contact")
async def public_contact(payload: ContactSubmission, request: Request) -> Any:
    _rate_limit_check(_client_ip(request))
    body = (
        "New contact form submission via trusyn.io/contact:\n\n"
        f"Name:         {payload.name}\n"
        f"Email:        {payload.email}\n"
        f"Organization: {payload.organization or '—'}\n"
        f"Source IP:    {_client_ip(request)}\n\n"
        f"Message:\n{payload.message}\n"
    )
    await _send_internal_mail(
        subject=f"[Trusyn contact] {payload.name} ({payload.organization or '—'})",
        body=body,
        reply_to=payload.email,
    )
    return {"status": "received"}


@router.post("/report")
async def public_spam_report(payload: SpamReportSubmission, request: Request) -> Any:
    _rate_limit_check(_client_ip(request))
    body = (
        "New public phishing/spam report submitted via trusyn.io/report:\n\n"
        f"Suspicious URL:      {payload.suspicious_url}\n"
        f"Impersonated brand:  {payload.impersonated_brand or '—'}\n"
        f"Reporter email:      {payload.reporter_email or 'anonymous'}\n"
        f"Source IP:           {_client_ip(request)}\n\n"
        f"Notes:\n{payload.notes or '—'}\n"
    )
    await _send_internal_mail(
        subject=f"[Trusyn public report] {payload.suspicious_url[:80]}",
        body=body,
        reply_to=payload.reporter_email,
    )
    return {"status": "received"}
