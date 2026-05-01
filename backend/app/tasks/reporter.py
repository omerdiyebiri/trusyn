"""
Celery task that orchestrates abuse-report dispatch for an incident.

Pipeline:
  1. Load incident + brand + parsed WHOIS
  2. Resolve origin IP (best-effort; None if behind Cloudflare)
  3. Determine threat type → choose templates
       - PHISHING / BRAND_IMPERSONATION:
           * Hosting report (always, if hosting abuse contact resolvable)
           * Registrar report (RAA §3.18)
           * Cloudflare backstop email (if site is on CF)
           * Google Safe Browsing (form-only audit log)
       - TYPOSQUATTING:
           * Typosquat soft notice to registrar only
  4. For each rendered report, persist a Report row, then send via SMTP, then
     update Report.status with the dispatch result.

Rate-limit:
  - Global cap of 30 messages / minute (across all incidents)
  - Per-recipient-domain cooldown of 30 seconds between successive sends
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Optional

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.models import (
    Incident,
    IncidentStatus,
    RecipientType,
    Report,
    ReportStatus,
    ThreatType,
)
from app.services.abuse_service import (
    RenderedReport,
    abuse_service,
)
from app.services.origin_ip_service import (
    discover_origin_ip,
    is_cloudflare_ns,
)
from app.services.provider_registry import (
    fallback_abuse_email,
    lookup_hosting,
    lookup_registrar,
)


logger = logging.getLogger(__name__)


# Per-recipient-domain cooldown (seconds since last send)
_recipient_last_send: dict = defaultdict(lambda: 0.0)
PER_RECIPIENT_COOLDOWN_SECONDS = 30
GLOBAL_RATE_PER_MINUTE = 30
_global_window: list = []


def _parse_whois_blob(raw: str) -> dict:
    """The legacy code stored str(dict) — accept that and fall back to ast.literal_eval."""
    if not raw:
        return {}
    try:
        import ast
        parsed = ast.literal_eval(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _first(value):
    """WHOIS fields are sometimes lists. Normalize to a single string."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return str(value)


async def _wait_for_recipient(recipient_email: str) -> None:
    """Enforce per-recipient and global rate limits."""
    now = time.time()
    # Global window
    cutoff = now - 60
    while _global_window and _global_window[0] < cutoff:
        _global_window.pop(0)
    if len(_global_window) >= GLOBAL_RATE_PER_MINUTE:
        delay = 60 - (now - _global_window[0]) + 0.1
        if delay > 0:
            await asyncio.sleep(delay)
    # Per-recipient
    if recipient_email:
        recipient_domain = recipient_email.split("@", 1)[-1].lower()
        last = _recipient_last_send[recipient_domain]
        wait = PER_RECIPIENT_COOLDOWN_SECONDS - (time.time() - last)
        if wait > 0:
            await asyncio.sleep(wait)
        _recipient_last_send[recipient_domain] = time.time()
    _global_window.append(time.time())


async def _persist_and_send(db, incident: Incident,
                            rendered: RenderedReport,
                            registrar_or_host_name: Optional[str]) -> None:
    """Insert the Report row, send the email, then update the row with results."""
    report = Report(
        incident_id=incident.id,
        recipient_type=rendered.recipient_type,
        recipient_email=rendered.recipient_email,
        recipient_form_url=rendered.recipient_form_url,
        recipient_name=registrar_or_host_name,
        subject=rendered.subject,
        message_id=rendered.extra_headers.get("Message-ID"),
        status=ReportStatus.PENDING,
        raw_content=rendered.body,
    )
    db.add(report)
    await db.flush()

    if rendered.recipient_email:
        await _wait_for_recipient(rendered.recipient_email)

    result = await abuse_service.send(rendered)
    if result["status"] == "sent":
        report.status = ReportStatus.SENT
        report.message_id = result["message_id"] or report.message_id
    elif result["status"] == "form_only":
        report.status = ReportStatus.FORM_ONLY
    else:
        report.status = ReportStatus.FAILED
        report.error_message = result.get("error")

    await db.commit()


async def send_abuse_reports_async(incident_id: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Incident)
            .options(selectinload(Incident.brand))
            .where(Incident.id == incident_id)
        )
        incident = result.scalars().first()
        if not incident or not incident.brand:
            logger.warning("send_abuse_reports: incident %s not found", incident_id)
            return
        brand = incident.brand

        whois_data = _parse_whois_blob(incident.whois_raw or "")
        registrar_field = _first(whois_data.get("registrar"))
        ns_records = whois_data.get("name_servers")
        registrar_email_from_whois = None
        emails = whois_data.get("emails")
        if emails:
            if isinstance(emails, str):
                emails = [emails]
            for e in emails:
                if "abuse" in e.lower():
                    registrar_email_from_whois = e
                    break
            if not registrar_email_from_whois and emails:
                registrar_email_from_whois = emails[0]
        created_at = _first(whois_data.get("creation_date"))

        domain = (incident.target_url.split("//", 1)[-1].split("/", 1)[0]
                  if incident.target_url else "")
        origin_ip = await discover_origin_ip(domain, ns_records)
        on_cloudflare = is_cloudflare_ns(ns_records)

        # ---- Resolve registrar abuse channel ----
        registrar_entry = lookup_registrar(registrar_field)
        if registrar_entry:
            r_name, r_email, r_form, _ = registrar_entry
        else:
            r_name = registrar_field or "the registrar"
            r_email = registrar_email_from_whois
            r_form = None

        # ---- Resolve hosting abuse channel ----
        hosting_entry = None
        host_org = _first(whois_data.get("org"))
        if host_org:
            hosting_entry = lookup_hosting(host_org)
        if hosting_entry:
            h_name, h_email, h_form, _ = hosting_entry
        else:
            # If we can't resolve, fall back to abuse@<reverse-dns-org>
            h_name = host_org or "the hosting provider"
            h_email = (registrar_email_from_whois
                       or (fallback_abuse_email(host_org) if host_org else None))
            h_form = None

        # ---- Dispatch by threat type ----
        if incident.threat_type == ThreatType.TYPOSQUATTING:
            rendered = abuse_service.render_typosquat(
                incident, brand, r_name, r_email, r_form,
                created_at, incident.confidence_score,
            )
            await _persist_and_send(db, incident, rendered, r_name)
        else:
            # Phishing / Brand impersonation flow
            if h_email or h_form:
                rendered = abuse_service.render_hosting(
                    incident, brand, h_email or "", h_form,
                    origin_ip or "undisclosed",
                )
                await _persist_and_send(db, incident, rendered, h_name)

            if r_email or r_form:
                rendered = abuse_service.render_registrar(
                    incident, brand, r_name, r_email, r_form,
                    origin_ip, created_at,
                )
                await _persist_and_send(db, incident, rendered, r_name)

            if on_cloudflare:
                rendered = abuse_service.render_cloudflare(incident, brand, origin_ip)
                await _persist_and_send(db, incident, rendered, "Cloudflare")

            # Google Safe Browsing — form-only audit log row
            rendered = abuse_service.render_google_safebrowsing(incident, brand)
            await _persist_and_send(db, incident, rendered, "Google Safe Browsing")

        # Mark incident as REPORTED if we sent at least one report
        result = await db.execute(
            select(Report).where(Report.incident_id == incident.id)
        )
        if result.scalars().first():
            incident.status = IncidentStatus.REPORTED
            await db.commit()


@celery_app.task(name="app.tasks.reporter.send_abuse_reports")
def send_abuse_reports(incident_id: str):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("loop closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        asyncio.ensure_future(send_abuse_reports_async(incident_id))
    else:
        loop.run_until_complete(send_abuse_reports_async(incident_id))
