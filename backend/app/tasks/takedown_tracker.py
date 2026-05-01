import imaplib
import email
from email.header import decode_header
import logging
import re
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.models import Incident, IncidentStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

def check_for_takedowns():
    """
    Periodically checks the takedowns@trusyn.io inbox for confirmation emails.
    """
    if not settings.IMAP_PASSWORD:
        logger.warning("IMAP_PASSWORD not configured. Skipping takedown check.")
        return

    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        mail.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        mail.select("inbox")

        # Search for all emails
        status, messages = mail.search(None, 'ALL')
        if status != "OK":
            return

        for num in messages[0].split():
            status, data = mail.fetch(num, "(RFC822)")
            if status != "OK": continue
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # 1. Get Subject and Body
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
            else:
                body = msg.get_payload(decode=True).decode()

            # 2. Look for Incident ID (TRUSYN-ID-XXXX) or Domain in body
            # Simple keyword matching for now
            takedown_keywords = ["suspended", "taken down", "removed", "resolved", "disabled", "takedown successful"]
            
            if any(kw in body.lower() for kw in takedown_keywords):
                # Attempt to find the domain in the email to match with an incident
                # This is a simplified matching logic
                for incident_status_to_update in [IncidentStatus.VALIDATED, IncidentStatus.REPORTED]:
                    # logic to match and update DB goes here (requires async loop)
                    pass

        mail.logout()
    except Exception as e:
        logger.error(f"IMAP Error: {e}")

async def sync_takedown_status():
    """Async wrapper for the IMAP tracker."""
    # This would involve an async loop to update DB records
    # Implementation planned for next step
    pass
