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
    VekaletStatus,
)
from app.services.abuse_service import (
    RenderedReport,
    abuse_service,
)
from app.services.cloudflare_abuse_service import (
    is_configured as cf_is_configured,
    submit_phishing_report as cf_submit_phishing_report,
    url_scanner_scan as cf_url_scanner_scan,
)
from app.services.intel_service import (
    submit_threatfox,
    submit_urlscan,
)
from app.services.origin_ip_service import (
    discover_origin_ip,
    is_cloudflare_ns,
    lookup_ip_org,
    resolve_a_records,
)
from app.services.provider_registry import (
    derive_registrar_abuse_email,
    fallback_abuse_email,
    lookup_hosting,
    lookup_registrar,
)
from app.services.whois_service import whois_service


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


def _build_cf_justification(
    incident: Incident,
    brand,
    intel_links: dict,
    origin_ip: Optional[str],
    cf_scan_uuid: Optional[str],
) -> str:
    """Build the `comments` field for a CF abuse report. Pack everything
    CF's auto-resolve classifier reads — citations to URLScan/ThreatFox,
    CF's own URL Scanner UUID, brand authority, origin IP, evidence
    pointers — in <5000 chars."""
    band = ("HIGH" if (incident.confidence_score or 0) >= 0.85
            else "MEDIUM" if (incident.confidence_score or 0) >= 0.5
            else "LOW")
    lines = [
        f"Phishing site impersonating brand: {brand.name}.",
        f"Legitimate site: {brand.official_domains or 'N/A'}.",
        f"Detection confidence: {band} "
        f"({(incident.confidence_score or 0):.2f}).",
        "",
        "Trusyn pipeline observations:",
        f"  - Threat type: {(incident.threat_type.value if incident.threat_type else 'phishing')}",
        f"  - Reported URL: {incident.target_url}",
        f"  - Origin host IP (if disclosed): {origin_ip or 'undisclosed (CF proxy)'}",
        f"  - Public Trusyn incident page: https://trusyn.io/incident/{incident.id}",
    ]
    if cf_scan_uuid:
        lines.append(
            f"  - Cloudflare URL Scanner pre-flight: "
            f"https://radar.cloudflare.com/scan/{cf_scan_uuid}"
        )
    if intel_links.get("urlscan"):
        lines.append(f"  - URLScan.io public scan: {intel_links['urlscan']}")
    if intel_links.get("threatfox"):
        lines.append(
            f"  - abuse.ch ThreatFox IOC: {intel_links['threatfox']}"
        )
    lines += [
        "",
        "Evidence captured:",
        "  - Full-page screenshot (mobile viewport, Turkish locale)",
        "  - DOM snapshot at detection",
        "  - WHOIS / RDAP record for the domain",
        "",
        "Requested action: take down the phishing content and disclose the",
        "origin host IP under the Cloudflare Trusted Reporter / abuse",
        "process so we can escalate to the upstream provider.",
    ]
    if getattr(brand, "vekalet_status", None) == "approved":
        lines += [
            "",
            "Power of attorney from the rights holder is on file at:",
            f"  https://api.trusyn.io/api/v1/public/incidents/{incident.id}/vekalet",
        ]
    return "\n".join(lines)[:5000]


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

    result = await abuse_service.send(rendered, incident=incident)
    if result["status"] == "sent":
        report.status = ReportStatus.SENT
        report.message_id = result["message_id"] or report.message_id
        attached = result.get("attachments") or []
        if attached:
            report.error_message = "attachments: " + ", ".join(attached)
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

        # Vekalet gate — registrars and hosting providers can lawfully reject a
        # takedown request from a third party that has not produced a power of
        # attorney from the brand owner. Block dispatch unless an admin has
        # approved the uploaded document, and persist a PENDING_REVIEW audit
        # row so the user can see why nothing went out.
        if (brand.vekalet_status or VekaletStatus.NOT_UPLOADED.value) != \
                VekaletStatus.APPROVED.value:
            logger.warning(
                "send_abuse_reports: brand %s vekalet not approved (status=%s) — skipping",
                brand.id, brand.vekalet_status,
            )
            audit = Report(
                incident_id=incident.id,
                recipient_type=RecipientType.HOSTING,
                recipient_email=None,
                recipient_name="Trusyn",
                subject="Awaiting power-of-attorney approval",
                status=ReportStatus.PENDING_REVIEW,
                error_message=(
                    f"Brand vekalet status is "
                    f"'{brand.vekalet_status or 'not_uploaded'}'. "
                    "Upload a signed power-of-attorney PDF and wait for admin "
                    "approval before dispatching abuse reports."
                ),
                raw_content="",
            )
            db.add(audit)
            await db.commit()
            return

        whois_data = _parse_whois_blob(incident.whois_raw or "")
        # Run-time fallback: if scanner's whois pass returned nothing or pre-RDAP
        # data is missing key fields, retry with the current whois_service
        # (which now has RDAP first).
        if not whois_data or not whois_data.get("registrar"):
            domain_for_whois = (
                incident.target_url.split("//", 1)[-1].split("/", 1)[0]
                if incident.target_url else ""
            )
            fresh = await asyncio.get_event_loop().run_in_executor(
                None, whois_service.get_domain_info, domain_for_whois
            )
            if fresh:
                whois_data = fresh
                incident.whois_raw = str(fresh)
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
            # Form-only registries (e.g. Dynadot, Porkbun, OVH) still publish
            # an abuse address in WHOIS — fall back to that so the takedown
            # request actually lands in someone's inbox in addition to the
            # operator filing the form. Many providers route the form into
            # the same queue as the email, but redundancy never hurts.
            if not r_email and registrar_email_from_whois:
                r_email = registrar_email_from_whois
        else:
            r_name = registrar_field or "the registrar"
            r_email = registrar_email_from_whois
            r_form = None
            # Modern registrars often redact contact info in RDAP. When the
            # registry has no entry AND WHOIS gave us nothing, derive an
            # abuse@<registrar-domain> guess so dispatch isn't silently
            # skipped (covers e.g. Spaceship before it was added to the
            # registry).
            if not r_email and registrar_field:
                r_email = derive_registrar_abuse_email(registrar_field)

        # ---- Resolve hosting abuse channel ----
        # Prefer IP RDAP lookup (gives the actual hosting org/AS), fall back to
        # WHOIS .org field (which is usually the registrar, not the host).
        hosting_entry = None
        ip_for_lookup = origin_ip
        if not ip_for_lookup:
            a_records = await resolve_a_records(domain)
            if a_records:
                ip_for_lookup = a_records[0]
        ip_org, ip_abuse = (None, None)
        if ip_for_lookup:
            ip_org, ip_abuse = await asyncio.get_event_loop().run_in_executor(
                None, lookup_ip_org, ip_for_lookup
            )
        host_org = ip_org or _first(whois_data.get("org"))
        # If the public-facing IP is Cloudflare's edge, the *real* host is
        # behind a CF proxy. Sending a "Phishing on your network" mail to
        # abuse@cloudflare.com is a duplicate of the CF backstop we send
        # below — and CF rightly ignores duplicates. Suppress the hosting
        # render in that case; the CF mail covers it.
        ip_org_lower = (ip_org or "").lower()
        is_cf_origin = "cloudflare" in ip_org_lower
        # If IP RDAP lands on Cloudflare even when NS isn't, it's still a CF
        # property and the CF backstop is the right channel.
        if is_cf_origin:
            on_cloudflare = True
        if host_org and not is_cf_origin:
            hosting_entry = lookup_hosting(host_org)
        if hosting_entry:
            h_name, h_email, h_form, _ = hosting_entry
            # Prefer IP-RDAP-derived abuse email when registry knows it
            if ip_abuse:
                h_email = ip_abuse
        elif is_cf_origin:
            # Hosting channel intentionally suppressed; CF backstop handles it.
            h_name, h_email, h_form = "Cloudflare", None, None
        else:
            h_name = host_org or "the hosting provider"
            h_email = ip_abuse or (
                fallback_abuse_email(host_org) if host_org else None
            )
            h_form = None

        # ---- Dispatch by threat type ----
        if incident.threat_type == ThreatType.TYPOSQUATTING:
            rendered = abuse_service.render_typosquat(
                incident, brand, r_name, r_email, r_form,
                created_at, incident.confidence_score,
            )
            await _persist_and_send(db, incident, rendered, r_name)
        else:
            # ---- Submit to threat-intel platforms FIRST so the public links
            #      can be cited in the hosting / registrar emails.
            loop = asyncio.get_event_loop()
            urlscan_result = await loop.run_in_executor(
                None, submit_urlscan, incident.target_url, brand.name,
            )
            threatfox_result = await loop.run_in_executor(
                None, submit_threatfox, incident.target_url, brand.name,
            )
            intel_links = {}
            if urlscan_result.get("public_url"):
                intel_links["urlscan"] = urlscan_result["public_url"]
            if threatfox_result.get("public_url"):
                intel_links["threatfox"] = threatfox_result["public_url"]

            # Phishing / Brand impersonation flow
            if h_email or h_form:
                rendered = abuse_service.render_hosting(
                    incident, brand, h_email or "", h_form,
                    origin_ip or "undisclosed",
                    intel_links=intel_links,
                )
                await _persist_and_send(db, incident, rendered, h_name)

            if r_email or r_form:
                rendered = abuse_service.render_registrar(
                    incident, brand, r_name, r_email, r_form,
                    origin_ip, created_at,
                    intel_links=intel_links,
                )
                await _persist_and_send(db, incident, rendered, r_name)

            if on_cloudflare:
                # Primary path: CF Abuse Reports API. Bypasses Turnstile,
                # feeds the same triage pipeline as the form. Email to
                # abuse@cloudflare.com is decorative; CF documents that
                # they auto-bounce email submissions back to the form.
                cf_api_succeeded = False
                if cf_is_configured():
                    cf_scan = await asyncio.get_event_loop().run_in_executor(
                        None, cf_url_scanner_scan, incident.target_url,
                    )
                    cf_result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: cf_submit_phishing_report(
                            target_urls=[incident.target_url],
                            brand_name=brand.name or "the customer brand",
                            justification=_build_cf_justification(
                                incident, brand, intel_links, origin_ip,
                                cf_scan.get("uuid"),
                            ),
                        ),
                    )
                    cf_audit = abuse_service.render_cloudflare_api_audit(
                        incident, brand,
                        cf_result.get("report_id"),
                        cf_result.get("status"),
                        cf_result.get("error"),
                        cf_scan.get("uuid"),
                    )
                    await _persist_and_send(db, incident, cf_audit, "Cloudflare")
                    cf_api_succeeded = cf_result.get("status") == "submitted"

                # Email backstop: send when API call wasn't attempted (no
                # creds) OR when it failed (so we don't leave CF empty-
                # handed while the API access issue is being resolved).
                # CF treats this as decorative but it's better than nothing.
                if not cf_api_succeeded:
                    rendered = abuse_service.render_cloudflare(
                        incident, brand, origin_ip)
                    await _persist_and_send(db, incident, rendered, "Cloudflare")

            # ---- Audit rows for intel platforms + form-only submissions ----
            us_audit = abuse_service.render_urlscan_audit(
                incident, brand,
                urlscan_result.get("uuid"),
                urlscan_result.get("public_url"),
                urlscan_result.get("error"),
            )
            await _persist_and_send(db, incident, us_audit, "URLScan.io")

            tf_audit = abuse_service.render_threatfox_audit(
                incident, brand,
                threatfox_result.get("uuid"),
                threatfox_result.get("public_url"),
                threatfox_result.get("error"),
            )
            await _persist_and_send(db, incident, tf_audit, "abuse.ch ThreatFox")

            ms_audit = abuse_service.render_microsoft_smartscreen(incident, brand)
            await _persist_and_send(db, incident, ms_audit, "Microsoft SmartScreen")

            gsb_audit = abuse_service.render_google_safebrowsing(incident, brand)
            await _persist_and_send(db, incident, gsb_audit, "Google Safe Browsing")

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
