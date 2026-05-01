"""
Abuse-report service.

Renders the five Trusyn templates documented in docs/abuse-research/templates.md
and dispatches them via SMTP with proper RFC 5322 headers
(Message-ID, Precedence: bulk, Auto-Submitted: auto-generated, X-Trusyn-* tracking
headers). All renders are plain-text only.

Templates rendered here:
- HOSTING_PHISHING (to hosting abuse desk)
- REGISTRAR_PHISHING (to registrar abuse desk; cites ICANN RAA Section 3.18)
- CF_PHISHING (Cloudflare email backstop; the form submission is the actual lever)
- TYPOSQUAT (registrar tone, less aggressive, UDRP-flavor)
- GOOGLE_SAFEBROWSING (form-only — we render a field map for the operator/Playwright)
"""

import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from typing import Any, Dict, List, Optional

import aiosmtplib

from app.core.config import settings
from app.models.models import Brand, Incident, RecipientType, ThreatType


logger = logging.getLogger(__name__)


@dataclass
class RenderedReport:
    recipient_type: RecipientType
    recipient_email: Optional[str]   # None = form-only (e.g. Google Safe Browsing)
    recipient_form_url: Optional[str]
    subject: str
    body: str
    extra_headers: Dict[str, str]
    attach_evidence: bool = True  # screenshot + WHOIS + DOM as attachments


def defang(url: str) -> str:
    """Convert http(s)://example.com → hxxp(s)://example[.]com."""
    if not url:
        return url
    return url.replace("http", "hxxp").replace(".", "[.]")


def short_id(incident_id) -> str:
    """First 8 hex chars of an incident UUID — used in subject brackets."""
    return str(incident_id).replace("-", "")[:8]


def domain_of(url: str) -> str:
    if not url:
        return ""
    rest = url.split("//", 1)[-1]
    return rest.split("/", 1)[0].split("?", 1)[0]


def confidence_band(score: Optional[float]) -> str:
    """Map a confidence_score (0..1) to a categorical label that abuse desks
    interpret well. Sub-band granularity is hidden because raw scores read
    as 'auto-tooling output' to humans on the receiving end."""
    if score is None:
        return "UNRATED"
    if score >= 0.85:
        return "HIGH"
    if score >= 0.5:
        return "MEDIUM"
    return "LOW"


def vekalet_block(incident: Incident, brand: Brand, indent: str = "  - ") -> str:
    """Render a single line linking to the public PoA download — only when
    the brand has an admin-approved vekalet on file. Returns an empty string
    otherwise so the surrounding template is unaffected. Avoids advertising
    a 404 URL to abuse desks for brands that don't have one yet."""
    status = getattr(brand, "vekalet_status", None)
    if status != "approved":
        return ""
    return (
        f"{indent}Power of attorney from {brand.name}: "
        f"https://trusyn.io/api/v1/public/incidents/{incident.id}/vekalet\n"
    )


def confidence_explanation(threat_type, score: Optional[float]) -> str:
    """Human-readable rationale paired with the band, suitable for inline
    inclusion in mail body. Does not expose raw decimal."""
    band = confidence_band(score)
    if threat_type and threat_type.value == "typosquatting":
        return f"{band} (Levenshtein similarity to brand domain: {score:.2f})" if score is not None else band
    if threat_type and threat_type.value == "phishing":
        return f"{band} (visual + DOM + brand-asset match)"
    return f"{band} (brand impersonation indicators)"


class AbuseService:
    # --- header generation ----------------------------------------------------

    def _common_headers(self, incident: Incident, brand: Brand,
                        report_type: str) -> Dict[str, str]:
        msg_id = make_msgid(domain="trusyn.io")
        return {
            "Message-ID": msg_id,
            "Date": format_datetime(datetime.now(timezone.utc)),
            "Precedence": "bulk",
            "Auto-Submitted": "auto-generated",
            "X-Trusyn-Incident-ID": str(incident.id),
            "X-Trusyn-Brand": brand.name or "",
            "X-Trusyn-Report-Type": report_type,
        }

    # --- template renderers ---------------------------------------------------

    def render_hosting(self, incident: Incident, brand: Brand,
                       hosting_email: str, hosting_form_url: Optional[str],
                       origin_ip: str,
                       intel_links: Optional[Dict[str, str]] = None) -> RenderedReport:
        domain = domain_of(incident.target_url)
        subject = f"[Trusyn-{short_id(incident.id)}] Phishing on your network: {domain}"
        country_restrictions = (getattr(brand, "country_restrictions", None)
                                or "Worldwide")
        confidence = confidence_explanation(incident.threat_type,
                                            incident.confidence_score)
        intel_block = ""
        if intel_links:
            lines = []
            if intel_links.get("urlscan"):
                lines.append(f"  - URLScan.io public scan: {intel_links['urlscan']}")
            if intel_links.get("threatfox"):
                lines.append(f"  - abuse.ch ThreatFox IOC:  {intel_links['threatfox']}")
            if lines:
                intel_block = ("\nIndependent verification (publicly inspectable, "
                               "no Trusyn login required):\n" + "\n".join(lines) + "\n")
        body = (
            "Dear Sir or Madam,\n\n"
            f"You are currently hosting a phishing attack on your network at {origin_ip}:\n\n"
            f"  {incident.target_url}\n\n"
            f"This attack impersonates our customer {brand.name} (legitimate site:\n"
            f"{brand.official_domains}). The fraudulent page collects credentials\n"
            "and financial data from victims who arrive via SMS, email or paid ads.\n\n"
            f"Confidence: {confidence}\n\n"
            "You can verify the content at the origin with:\n\n"
            f"  curl -v -H \"Host: {domain}\" {origin_ip}/\n"
            f"{intel_block}\n"
            "Evidence (attached to this message):\n"
            f"  - trusyn-evidence-{short_id(incident.id)}.png — full-page screenshot\n"
            f"  - trusyn-dom-{short_id(incident.id)}.html — DOM snapshot at detection\n"
            f"  - trusyn-whois-{short_id(incident.id)}.txt — WHOIS / RDAP record\n"
            f"  - Public Trusyn incident: https://trusyn.io/incident/{incident.id}\n"
            f"{vekalet_block(incident, brand)}"
            "\n"
            "It is possible the attack is geo-restricted; please confirm the page\n"
            "cannot be viewed from these regions before deciding it is resolved:\n"
            f"{country_restrictions}\n\n"
            "Please remove this fraudulent content as soon as possible. We ask that\n"
            f"you preserve the content and access logs so that {brand.name} and law\n"
            "enforcement can investigate further once the page is offline.\n\n"
            "We will follow up in 72 hours if the page is still live.\n\n"
            "Regards,\n"
            f"Trusyn Brand Protection (on behalf of {brand.name})\n"
            f"{settings.EMAILS_FROM_EMAIL}\n"
            f"Incident ID: {incident.id}\n"
        )
        return RenderedReport(
            recipient_type=RecipientType.HOSTING,
            recipient_email=hosting_email,
            recipient_form_url=hosting_form_url,
            subject=subject,
            body=body,
            extra_headers=self._common_headers(incident, brand, "phishing"),
        )

    def render_registrar(self, incident: Incident, brand: Brand,
                         registrar_name: str, registrar_email: Optional[str],
                         registrar_form_url: Optional[str],
                         origin_ip: Optional[str],
                         created_at: Optional[str],
                         intel_links: Optional[Dict[str, str]] = None) -> RenderedReport:
        domain = domain_of(incident.target_url)
        subject = (f"[Trusyn-{short_id(incident.id)}] DNS Abuse (phishing) — "
                   f"{domain} — RAA §3.18")
        confidence = confidence_explanation(incident.threat_type,
                                            incident.confidence_score)
        intel_block = ""
        if intel_links:
            lines = []
            if intel_links.get("urlscan"):
                lines.append(f"  - URLScan.io public scan: {intel_links['urlscan']}")
            if intel_links.get("threatfox"):
                lines.append(f"  - abuse.ch ThreatFox IOC:  {intel_links['threatfox']}")
            if lines:
                intel_block = ("\nIndependent verification (publicly inspectable, "
                               "no Trusyn login required):\n" + "\n".join(lines) + "\n")
        body = (
            f"To the Abuse Department of {registrar_name},\n\n"
            "This is a formal notice of well-evidenced DNS Abuse at the following\n"
            "domain registered through your services:\n\n"
            f"  Domain:        {domain}\n"
            f"  Phishing URL:  {incident.target_url}\n"
            f"  Registered:    {created_at or 'see attached WHOIS'}\n"
            f"  Confidence:    {confidence}\n\n"
            "The domain is being used to conduct a phishing attack impersonating\n"
            f"our customer {brand.name} ({brand.official_domains}). Under the 2024\n"
            "amendments to the ICANN Registrar Accreditation Agreement (Section\n"
            "3.18, effective 5 April 2024), registrars are required to take prompt\n"
            "mitigation action against well-evidenced DNS Abuse, of which phishing\n"
            f"is an enumerated category.\n{intel_block}\n"
            "Evidence (attached to this message):\n"
            f"  - trusyn-evidence-{short_id(incident.id)}.png — full-page screenshot\n"
            f"  - trusyn-dom-{short_id(incident.id)}.html — credential-harvesting DOM\n"
            f"  - trusyn-whois-{short_id(incident.id)}.txt — WHOIS / RDAP record\n"
            f"  - Hosting origin IP: {origin_ip or 'undisclosed (CF proxy)'}\n"
            f"  - Public Trusyn incident: https://trusyn.io/incident/{incident.id}\n"
            f"{vekalet_block(incident, brand)}"
            "\n"
            f"Requested action: suspension of {domain} (clientHold or serverHold)\n"
            f"and a confirming response to {settings.EMAILS_FROM_EMAIL}.\n\n"
            f"Please cite incident {incident.id} in any correspondence.\n\n"
            "Regards,\n"
            f"Trusyn Brand Protection (on behalf of {brand.name})\n"
            f"{settings.EMAILS_FROM_EMAIL}\n"
        )
        return RenderedReport(
            recipient_type=RecipientType.REGISTRAR,
            recipient_email=registrar_email,
            recipient_form_url=registrar_form_url,
            subject=subject,
            body=body,
            extra_headers=self._common_headers(incident, brand, "phishing"),
        )

    def render_cloudflare(self, incident: Incident, brand: Brand,
                          origin_ip: Optional[str]) -> RenderedReport:
        domain = domain_of(incident.target_url)
        subject = (f"[Trusyn-{short_id(incident.id)}] Phishing report "
                   f"(form duplicate) — {domain}")
        body = (
            "Cloudflare Trust & Safety,\n\n"
            f"This message duplicates Trusyn incident {incident.id}, also filed\n"
            f"through the Cloudflare abuse form for {domain}.\n\n"
            f"  Reported URL:       {defang(incident.target_url)}\n"
            f"  Origin host IP:     {origin_ip or 'undisclosed'}\n"
            f"  Brand impersonated: {brand.name} ({brand.official_domains})\n"
            f"  Trusyn incident:    https://trusyn.io/incident/{incident.id}\n"
            f"{vekalet_block(incident, brand, indent='  Power of attorney:  ')}"
            "\n"
            "Evidence: DOM snapshot, screenshot, WHOIS record, DNS records.\n\n"
            "Submitted via form for action. This email is logged for audit only.\n\n"
            "Regards,\n"
            f"Trusyn Brand Protection (on behalf of {brand.name})\n"
            f"{settings.EMAILS_FROM_EMAIL}\n"
        )
        return RenderedReport(
            recipient_type=RecipientType.CLOUDFLARE,
            recipient_email="abuse@cloudflare.com",
            recipient_form_url="https://abuse.cloudflare.com/phishing",
            subject=subject,
            body=body,
            extra_headers=self._common_headers(incident, brand, "phishing"),
        )

    def render_typosquat(self, incident: Incident, brand: Brand,
                         registrar_name: str, registrar_email: Optional[str],
                         registrar_form_url: Optional[str],
                         created_at: Optional[str],
                         similarity: Optional[float]) -> RenderedReport:
        domain = domain_of(incident.target_url)
        subject = (f"[Trusyn-{short_id(incident.id)}] Typosquat / brand "
                   f"impersonation — {domain}")
        sim_str = (f"{similarity:.2f}" if similarity is not None else "N/A")
        body = (
            f"To the Abuse Department of {registrar_name},\n\n"
            f"Domain {domain} (registered {created_at or 'unknown'}) appears to\n"
            f"be a typosquat of our customer {brand.name} (legitimate site:\n"
            f"{brand.official_domains}).\n\n"
            f"Levenshtein similarity to {brand.name}'s primary domain: {sim_str}.\n\n"
            "We have not yet confirmed phishing activity at this address, but the\n"
            "registration is consistent with a typosquat intended to capture\n"
            "mistyped traffic and is grounds for a UDRP / trademark complaint by\n"
            "our customer.\n\n"
            "We are notifying you in good faith ahead of any UDRP filing so the\n"
            "registrant has an opportunity to comply voluntarily. Public incident:\n"
            f"https://trusyn.io/incident/{incident.id}.\n\n"
            "We do not request immediate suspension at this stage. We do request\n"
            f"that the abuse contact for {domain} be confirmed accurate and\n"
            "reachable so that any future UDRP / phishing notice (if the site\n"
            "escalates) can be acted on within ICANN RAA timelines.\n\n"
            "Regards,\n"
            f"Trusyn Brand Protection (on behalf of {brand.name})\n"
            f"{settings.EMAILS_FROM_EMAIL}\n"
        )
        return RenderedReport(
            recipient_type=RecipientType.REGISTRAR,
            recipient_email=registrar_email,
            recipient_form_url=registrar_form_url,
            subject=subject,
            body=body,
            extra_headers=self._common_headers(incident, brand, "typosquat"),
        )

    def render_urlscan_audit(self, incident: Incident, brand: Brand,
                             scan_uuid: Optional[str],
                             scan_url: Optional[str],
                             error: Optional[str]) -> RenderedReport:
        """Audit row capturing the URLScan.io submission outcome."""
        domain = domain_of(incident.target_url)
        subject = (f"[Trusyn-{short_id(incident.id)}] URLScan submission — "
                   f"{domain}")
        body = (
            "Audit log of URLScan.io submission.\n\n"
            f"Target URL:   {incident.target_url}\n"
            f"Brand:        {brand.name}\n"
            f"Scan UUID:    {scan_uuid or '—'}\n"
            f"Public URL:   {scan_url or '—'}\n"
            f"Error:        {error or '—'}\n\n"
            "URLScan publishes the rendered page, screenshots, network log,\n"
            "and certificate chain for the URL. The public URL above can be\n"
            "cited in subsequent abuse reports as independent evidence.\n"
        )
        return RenderedReport(
            recipient_type=RecipientType.URLSCAN,
            recipient_email=None,
            recipient_form_url=scan_url or "https://urlscan.io/",
            subject=subject,
            body=body,
            extra_headers=self._common_headers(incident, brand, "phishing"),
            attach_evidence=False,
        )

    def render_threatfox_audit(self, incident: Incident, brand: Brand,
                               ioc_id: Optional[str],
                               public_url: Optional[str],
                               error: Optional[str]) -> RenderedReport:
        """Audit row capturing the abuse.ch ThreatFox submission outcome."""
        domain = domain_of(incident.target_url)
        subject = (f"[Trusyn-{short_id(incident.id)}] ThreatFox IOC — "
                   f"{domain}")
        body = (
            "Audit log of abuse.ch ThreatFox submission.\n\n"
            f"Target URL:   {incident.target_url}\n"
            f"Brand:        {brand.name}\n"
            f"IOC ID:       {ioc_id or '—'}\n"
            f"Public URL:   {public_url or '—'}\n"
            f"Error:        {error or '—'}\n\n"
            "ThreatFox feeds Cisco Talos, McAfee, browser blockers, and the\n"
            "wider security community. The IOC is automatically distributed\n"
            "into the abuse.ch feeds.\n"
        )
        return RenderedReport(
            recipient_type=RecipientType.THREATFOX,
            recipient_email=None,
            recipient_form_url=public_url or "https://threatfox.abuse.ch/",
            subject=subject,
            body=body,
            extra_headers=self._common_headers(incident, brand, "phishing"),
            attach_evidence=False,
        )

    def render_microsoft_smartscreen(self, incident: Incident,
                                     brand: Brand) -> RenderedReport:
        """Form-only submission to Microsoft Defender SmartScreen — operator
        files via https://www.microsoft.com/en-us/wdsi/support/report-unsafe-site-guest"""
        domain = domain_of(incident.target_url)
        subject = (f"[Trusyn-{short_id(incident.id)}] SmartScreen submission "
                   f"— {domain}")
        body = (
            "Field map for Microsoft Defender SmartScreen unsafe-site form:\n"
            "  https://www.microsoft.com/en-us/wdsi/support/report-unsafe-site-guest\n\n"
            f"  Address (URL)                : {incident.target_url}\n"
            f"  Issue                        : Phishing\n"
            f"  Brand impersonated           : {brand.name}\n"
            f"  Comments                     : Trusyn incident {incident.id}\n\n"
            "Submission via the form propagates to Microsoft Edge,\n"
            "Outlook safe links, and Defender for Endpoint.\n"
        )
        return RenderedReport(
            recipient_type=RecipientType.MICROSOFT_SMARTSCREEN,
            recipient_email=None,
            recipient_form_url="https://www.microsoft.com/en-us/wdsi/support/report-unsafe-site-guest",
            subject=subject,
            body=body,
            extra_headers=self._common_headers(incident, brand, "phishing"),
            attach_evidence=False,
        )

    def render_google_safebrowsing(self, incident: Incident,
                                   brand: Brand) -> RenderedReport:
        """Form-only — we still render a body that the operator can paste into
        the form and that we can dispatch to the audit log inbox."""
        domain = domain_of(incident.target_url)
        subject = (f"[Trusyn-{short_id(incident.id)}] Safe Browsing submission "
                   f"— {domain}")
        body = (
            "Field map for https://safebrowsing.google.com/safebrowsing/report_phish/:\n\n"
            f"  URL                                : {incident.target_url}\n"
            f"  Email Address (optional)           : {settings.EMAILS_FROM_EMAIL}\n"
            f"  Subject of phishing email (opt.)   : (see incident bundle)\n"
            f"  Text of phishing email (optional)  : (see incident bundle)\n"
            f"  Organization being impersonated    : {brand.name}\n\n"
            "Submitted via form for action. This email is logged for audit only.\n\n"
            "Regards,\n"
            f"Trusyn Brand Protection (on behalf of {brand.name})\n"
            f"{settings.EMAILS_FROM_EMAIL}\n"
        )
        return RenderedReport(
            recipient_type=RecipientType.GOOGLE_SAFEBROWSING,
            recipient_email=None,  # form-only
            recipient_form_url="https://safebrowsing.google.com/safebrowsing/report_phish/",
            subject=subject,
            body=body,
            extra_headers=self._common_headers(incident, brand, "phishing"),
            attach_evidence=False,
        )

    # --- evidence attachments -------------------------------------------------

    @staticmethod
    def _resolve_storage_path(p: Optional[str]) -> Optional[str]:
        """Accept absolute paths as-is; resolve legacy relative paths against
        the canonical /app mount."""
        if not p:
            return None
        if os.path.isabs(p):
            return p
        return os.path.join("/app", p)

    def _attach_evidence(self, message: EmailMessage,
                         incident: Optional[Incident]) -> List[str]:
        """Attach screenshot.png, WHOIS.txt, and DOM.html (when present) to
        the outbound message. Returns the list of filenames actually attached
        for logging."""
        if not incident:
            return []
        attached: List[str] = []
        sid = short_id(incident.id)

        # Screenshot
        screenshot_path = self._resolve_storage_path(incident.screenshot_path)
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                with open(screenshot_path, "rb") as fh:
                    data = fh.read()
                message.add_attachment(
                    data, maintype="image", subtype="png",
                    filename=f"trusyn-evidence-{sid}.png",
                )
                attached.append(f"screenshot ({len(data)} bytes)")
            except Exception as exc:
                logger.warning("Failed to attach screenshot for %s: %s",
                               incident.id, exc)
        elif incident.screenshot_path:
            logger.warning("Screenshot path %s not found on disk for %s",
                           incident.screenshot_path, incident.id)

        # DOM snapshot — sibling .html in same dir as screenshot
        if screenshot_path:
            dom_path = screenshot_path.replace(".png", ".html")
            if os.path.exists(dom_path):
                try:
                    with open(dom_path, "rb") as fh:
                        data = fh.read()
                    message.add_attachment(
                        data, maintype="text", subtype="html",
                        filename=f"trusyn-dom-{sid}.html",
                    )
                    attached.append(f"DOM ({len(data)} bytes)")
                except Exception as exc:
                    logger.warning("Failed to attach DOM for %s: %s",
                                   incident.id, exc)

        # WHOIS as plain-text
        if incident.whois_raw:
            try:
                data = incident.whois_raw.encode("utf-8", errors="replace")
                message.add_attachment(
                    data, maintype="text", subtype="plain",
                    filename=f"trusyn-whois-{sid}.txt",
                )
                attached.append(f"WHOIS ({len(data)} bytes)")
            except Exception as exc:
                logger.warning("Failed to attach WHOIS for %s: %s",
                               incident.id, exc)

        return attached

    # --- delivery -------------------------------------------------------------

    async def send(self, report: RenderedReport,
                   incident: Optional[Incident] = None) -> Dict[str, Any]:
        """Dispatch a RenderedReport via SMTP. Returns a dict with status,
        message_id, and error (if any). Form-only recipients (no email) return
        status='form_only' without sending. Attachments (screenshot + WHOIS +
        DOM) are added for non-form-only recipients when incident is provided
        and report.attach_evidence is True."""
        if not report.recipient_email:
            return {"status": "form_only", "message_id": None, "error": None,
                    "attachments": []}

        if not settings.SMTP_HOST or not settings.SMTP_PASSWORD:
            return {"status": "failed", "message_id": None,
                    "error": "SMTP_HOST or SMTP_PASSWORD not configured",
                    "attachments": []}

        message = EmailMessage()
        message["From"] = (f"{settings.EMAILS_FROM_NAME} "
                           f"<{settings.EMAILS_FROM_EMAIL}>")
        message["To"] = report.recipient_email
        message["Reply-To"] = settings.EMAILS_FROM_EMAIL
        message["Subject"] = report.subject
        for k, v in report.extra_headers.items():
            message[k] = v
        message.set_content(report.body)

        attached: List[str] = []
        if report.attach_evidence and incident is not None:
            attached = self._attach_evidence(message, incident)

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=settings.SMTP_TLS,
            )
            return {"status": "sent", "message_id": message["Message-ID"],
                    "error": None, "attachments": attached}
        except Exception as exc:
            logger.error("SMTP send failed for %s: %s",
                         report.recipient_email, exc)
            return {"status": "failed", "message_id": message["Message-ID"],
                    "error": str(exc), "attachments": attached}


abuse_service = AbuseService()
