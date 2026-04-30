import json
from typing import Optional, Dict, Any
from app.models.models import Incident, Brand, RecipientType
import re

class AbuseService:
    @staticmethod
    def find_abuse_email(whois_data: Dict[str, Any]) -> Optional[str]:
        # Simple heuristic to find abuse email in whois data
        emails = whois_data.get("emails", [])
        if isinstance(emails, str):
            emails = [emails]
        
        # Look for emails containing 'abuse'
        for email in emails:
            if "abuse" in email.lower():
                return email
        
        # Fallback to first email if found
        if emails:
            return emails[0]
        return None

    @staticmethod
    def is_cloudflare(whois_data: Dict[str, Any]) -> bool:
        ns = whois_data.get("name_servers", [])
        if not ns:
            return False
        if isinstance(ns, str):
            ns = [ns]
        
        for server in ns:
            if "cloudflare.com" in server.lower():
                return True
        return False

    def prepare_hosting_report(self, incident: Incident, brand: Brand, abuse_email: str) -> Dict[str, str]:
        subject = f"Urgent: Phishing Activity Detected on {incident.target_url}"
        body = f"""Hello,

Phishing activity has been detected regarding {incident.target_url} hosted on your network.

Reporter: Trusyn Brand Protection
Reported URLs: {incident.target_url}
Target Brand: {brand.name}
Official URL: {brand.official_domains}

Please address this issue with your customer and remove the fraudulent content immediately.

Regards,
Trusyn Trust & Safety Team"""
        return {"subject": subject, "body": body, "recipient": abuse_email}

    def prepare_cloudflare_report(self, incident: Incident, brand: Brand) -> Dict[str, str]:
        subject = f"Phishing report received regarding {incident.target_url}"
        body = f"""Hello,
Cloudflare received a Phishing report regarding: {incident.target_url}.
Reported URLs: {incident.target_url}
Evidence: This site is impersonating {brand.name} (Official: {brand.official_domains}).

Please investigate and restrict access to the reported URL."""
        return {"subject": subject, "body": body, "recipient": "abuse@cloudflare.com"}

abuse_service = AbuseService()
