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
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from typing import Any, Dict, Optional

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
                       origin_ip: str) -> RenderedReport:
        domain = domain_of(incident.target_url)
        subject = f"[Trusyn-{short_id(incident.id)}] Phishing on your network: {domain}"
        country_restrictions = (getattr(brand, "country_restrictions", None)
                                or "Worldwide")
        body = (
            "Dear Sir or Madam,\n\n"
            f"You are currently hosting a phishing attack on your network at {origin_ip}:\n\n"
            f"  {incident.target_url}\n\n"
            f"This attack impersonates our customer {brand.name} (legitimate site:\n"
            f"{brand.official_domains}). The fraudulent page collects credentials\n"
            "and financial data from victims who arrive via SMS, email or paid ads.\n\n"
            "You can verify the content at the origin with:\n\n"
            f"  curl -v -H \"Host: {domain}\" {origin_ip}/\n\n"
            "Evidence we have collected:\n"
            "  - Full DOM snapshot\n"
            f"  - High-resolution screenshot (incident {short_id(incident.id)})\n"
            "  - WHOIS / RDAP record\n"
            "  - DNS A / MX / NS records at time of detection\n"
            f"  - Public Trusyn incident: https://trusyn.io/dashboard?incident={incident.id}\n\n"
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
                         created_at: Optional[str]) -> RenderedReport:
        domain = domain_of(incident.target_url)
        subject = (f"[Trusyn-{short_id(incident.id)}] DNS Abuse (phishing) — "
                   f"{domain} — RAA §3.18")
        body = (
            f"To the Abuse Department of {registrar_name},\n\n"
            "This is a formal notice of well-evidenced DNS Abuse at the following\n"
            "domain registered through your services:\n\n"
            f"  Domain:        {domain}\n"
            f"  Phishing URL:  {incident.target_url}\n"
            f"  Registered:    {created_at or 'see attached WHOIS'}\n\n"
            "The domain is being used to conduct a phishing attack impersonating\n"
            f"our customer {brand.name} ({brand.official_domains}). Under the 2024\n"
            "amendments to the ICANN Registrar Accreditation Agreement (Section\n"
            "3.18, effective 5 April 2024), registrars are required to take prompt\n"
            "mitigation action against well-evidenced DNS Abuse, of which phishing\n"
            "is an enumerated category.\n\n"
            "Evidence:\n"
            "  - DOM snapshot of the credential-harvesting page\n"
            f"  - High-resolution screenshot (incident {short_id(incident.id)})\n"
            f"  - Comparison of the imitated brand assets to {brand.official_domains}\n"
            "  - WHOIS / RDAP record\n"
            f"  - Hosting origin IP: {origin_ip or 'undisclosed (CF proxy)'}\n"
            f"  - Public Trusyn incident: https://trusyn.io/dashboard?incident={incident.id}\n\n"
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
            f"  Trusyn incident:    https://trusyn.io/dashboard?incident={incident.id}\n\n"
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
            f"https://trusyn.io/dashboard?incident={incident.id}.\n\n"
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
        )

    # --- delivery -------------------------------------------------------------

    async def send(self, report: RenderedReport) -> Dict[str, Any]:
        """Dispatch a RenderedReport via SMTP. Returns a dict with status,
        message_id, and error (if any). Form-only recipients (no email) return
        status='form_only' without sending.
        """
        if not report.recipient_email:
            return {"status": "form_only", "message_id": None, "error": None}

        if not settings.SMTP_HOST or not settings.SMTP_PASSWORD:
            return {"status": "failed", "message_id": None,
                    "error": "SMTP_HOST or SMTP_PASSWORD not configured"}

        message = EmailMessage()
        message["From"] = (f"{settings.EMAILS_FROM_NAME} "
                           f"<{settings.EMAILS_FROM_EMAIL}>")
        message["To"] = report.recipient_email
        message["Reply-To"] = settings.EMAILS_FROM_EMAIL
        message["Subject"] = report.subject
        for k, v in report.extra_headers.items():
            message[k] = v
        message.set_content(report.body)

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=settings.SMTP_TLS,
            )
            return {"status": "sent", "message_id": message["Message-ID"], "error": None}
        except Exception as exc:
            logger.error("SMTP send failed for %s: %s", report.recipient_email, exc)
            return {"status": "failed", "message_id": message["Message-ID"], "error": str(exc)}


abuse_service = AbuseService()
