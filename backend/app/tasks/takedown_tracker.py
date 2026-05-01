"""
Periodic IMAP scanner that updates Report rows based on replies received at
takedowns@trusyn.io. Matches replies to outbound reports via the
[Trusyn-<8hex>] subject token (preferred) or X-Trusyn-Incident-ID echoed in the
body / headers.

Closure-phrase regex hints come from docs/abuse-research/templates.md §7.
"""

import asyncio
import email
import imaplib
import logging
import re
from email.header import decode_header
from typing import List, Optional, Tuple

from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import (
    Incident,
    IncidentStatus,
    Report,
    ReportStatus,
)


logger = logging.getLogger(__name__)


SUBJECT_TOKEN_RE = re.compile(r"\[Trusyn-([a-f0-9]{8})\]", re.IGNORECASE)

ACTIONED_PATTERNS = [
    re.compile(r"restricted access to the reported url", re.IGNORECASE),
    re.compile(r"forwarded this complaint to your hosting provider", re.IGNORECASE),
    re.compile(r"domain (has been|was) (suspended|placed on (server|client)hold)", re.IGNORECASE),
    re.compile(r"(content has been|has been) (removed|disabled|taken offline)", re.IGNORECASE),
    re.compile(r"(suspended|terminated) (the|our) customer'?s? (account|service)", re.IGNORECASE),
    re.compile(r"netcraft issue number", re.IGNORECASE),
]

DECLINED_PATTERNS = [
    re.compile(r"unable to verify", re.IGNORECASE),
    re.compile(r"insufficient evidence", re.IGNORECASE),
    re.compile(r"please use our (web )?form", re.IGNORECASE),
    re.compile(r"this domain is not registered (with|by)", re.IGNORECASE),
]

BOUNCE_PATTERNS = [
    re.compile(r"^mail delivery subsystem", re.IGNORECASE | re.MULTILINE),
    re.compile(r"delivery has failed", re.IGNORECASE),
    re.compile(r"\b5\d{2}\b\s+(failed|rejected|undeliverable)", re.IGNORECASE),
]


def _decode(value) -> str:
    if not value:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return value.decode("latin-1", errors="replace")
    parts = []
    for chunk, enc in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts)


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    return _decode(payload)
        return ""
    payload = msg.get_payload(decode=True)
    return _decode(payload) if payload else ""


def _classify(subject: str, body: str) -> Tuple[ReportStatus, Optional[str]]:
    """Return (new_status, snippet_for_logging)."""
    haystack = f"{subject}\n{body}"
    for pat in BOUNCE_PATTERNS:
        m = pat.search(haystack)
        if m:
            return ReportStatus.FAILED, m.group(0)[:200]
    for pat in ACTIONED_PATTERNS:
        m = pat.search(haystack)
        if m:
            return ReportStatus.ACTIONED, m.group(0)[:200]
    for pat in DECLINED_PATTERNS:
        m = pat.search(haystack)
        if m:
            return ReportStatus.DECLINED, m.group(0)[:200]
    # Default: any reply is at least an acknowledgement
    return ReportStatus.RECEIVED, None


def _fetch_recent_messages() -> List[Tuple[str, str]]:
    """Connect to IMAP, return list of (subject, body) for messages in INBOX
    that we haven't yet flagged with our internal label."""
    if not settings.IMAP_PASSWORD:
        return []

    out: List[Tuple[str, str]] = []
    mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
    try:
        mail.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        mail.select("inbox")
        # Only look at recent unprocessed messages
        status, data = mail.search(None, '(UNSEEN)')
        if status != "OK":
            return []
        for num in data[0].split():
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = _decode(msg.get("Subject", ""))
            body = _extract_body(msg)
            out.append((subject, body))
            # Mark seen so we don't re-process
            mail.store(num, '+FLAGS', '\\Seen')
    finally:
        try:
            mail.logout()
        except Exception:
            pass
    return out


async def sync_takedown_status() -> dict:
    """Scan IMAP for replies and update matching Report rows."""
    summary = {"scanned": 0, "matched": 0, "updated": 0}
    if not settings.IMAP_PASSWORD:
        logger.warning("IMAP_PASSWORD not configured; skipping takedown sync")
        return summary

    try:
        loop = asyncio.get_event_loop()
        messages = await loop.run_in_executor(None, _fetch_recent_messages)
    except Exception as exc:
        logger.error("IMAP fetch failed: %s", exc)
        return summary
    summary["scanned"] = len(messages)
    if not messages:
        return summary

    async with AsyncSessionLocal() as db:
        for subject, body in messages:
            token_match = SUBJECT_TOKEN_RE.search(f"{subject}\n{body}")
            if not token_match:
                continue
            short = token_match.group(1).lower()
            # Find any incident whose ID starts with this 8-hex prefix
            result = await db.execute(select(Incident))
            incidents = result.scalars().all()
            target_incident = None
            for inc in incidents:
                if str(inc.id).replace("-", "").lower().startswith(short):
                    target_incident = inc
                    break
            if not target_incident:
                continue
            summary["matched"] += 1

            new_status, snippet = _classify(subject, body)

            result = await db.execute(
                select(Report).where(Report.incident_id == target_incident.id)
            )
            reports = result.scalars().all()
            for report in reports:
                if report.status not in (ReportStatus.SENT, ReportStatus.PENDING):
                    continue
                report.status = new_status
                if snippet:
                    report.error_message = snippet
                summary["updated"] += 1

            if new_status == ReportStatus.ACTIONED and target_incident.status not in (
                IncidentStatus.RESOLVED, IncidentStatus.FALSE_POSITIVE,
            ):
                target_incident.status = IncidentStatus.RESOLVED

        await db.commit()

    return summary
