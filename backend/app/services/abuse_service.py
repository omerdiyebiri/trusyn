import json
from typing import Optional, Dict, Any, List
from app.models.models import Incident, Brand, RecipientType
import re

class AbuseService:
    def obfuscate_url(self, url: str) -> str:
        """Masks URLs to prevent accidental clicks (e.g., http -> hxxp)."""
        return url.replace("http", "hxxp").replace(".", "[.]")

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

    def prepare_hosting_report(self, incident: Incident, brand: Brand, abuse_email: str, origin_ip: str = "Unknown") -> Dict[str, str]:
        """Generates a technical report for the hosting provider."""
        target_domain = incident.target_url.split("//")[-1].split("/")[0]
        obfuscated_url = self.obfuscate_url(incident.target_url)
        
        subject = f"Urgent: Phishing Activity Detected on {target_domain} - {origin_ip}"
        
        body = f"""Hello,

Cloudflare received a Phishing report regarding {target_domain}.

Please be aware Cloudflare offers network service solutions including pass-through security services, a content distribution network (CDN) and registrar services. Due to the pass-through nature of our services, our IP addresses appear in WHOIS and DNS records for websites using Cloudflare. Cloudflare is generally not a website hosting provider, and we cannot remove material from the Internet that is hosted by others.

The actual host for {target_domain} are the following IP addresses: {origin_ip}. 
Using the following command, you can confirm the site in question is hosted at that IP address: 
curl -v -H "Host: {target_domain}" {origin_ip}/

Below is the information we received:

Reporter: Trusyn Brand Protection
Reported URLs:
{obfuscated_url}

Logs or Evidence of Abuse: {incident.target_url} (Confidence Score: {incident.confidence_score})

Please address this issue with your customer and remove the fraudulent content immediately.

Regards,
Trusyn Trust & Safety Team (on behalf of {brand.name})"""
        
        return {"subject": subject, "body": body, "recipient": abuse_email}

    def prepare_cloudflare_report(self, incident: Incident, brand: Brand) -> Dict[str, str]:
        """Generates an automated report for Cloudflare Trust & Safety."""
        target_domain = incident.target_url.split("//")[-1].split("/")[0]
        obfuscated_url = self.obfuscate_url(incident.target_url)
        
        subject = f"[{str(incident.id)[:8]}]: Phishing report received regarding your site"
        
        body = f"""Hello,

Trusyn Brand Protection has detected a Phishing site behind Cloudflare: {target_domain}.

Report ID: {incident.id}
Logs or other evidence of abuse: {incident.target_url}

Reported URLs:
{obfuscated_url}

This site is impersonating our customer {brand.name} (Official: {brand.official_domains}).
We have already notified the hosting provider. Please restrict access to the reported URL(s) through your network services.

This report was handled automatically.

Regards,
Trusyn Trust & Safety"""
        
        return {"subject": subject, "body": body, "recipient": "abuse@cloudflare.com"}

    def prepare_registrar_report(self, incident: Incident, brand: Brand, registrar_name: str, registrar_email: str) -> Dict[str, str]:
        """Generates a legal/technical report for the Domain Registrar."""
        target_domain = incident.target_url.split("//")[-1].split("/")[0]
        obfuscated_url = self.obfuscate_url(incident.target_url)
        
        subject = f"Urgent: Phishing Infrastructure Notification - {target_domain} - {brand.name}"
        
        body = f"""To the Abuse Department of {registrar_name},

This is a formal notification regarding a domain registered through your services: {target_domain}.

Our security systems have identified that this domain is being used to facilitate a Phishing attack targeting our customer, {brand.name}. This activity constitutes a direct violation of your Anti-Abuse Policies and ICANN’s Registrar Accreditation Agreement (RAA) regarding security threats.

Incident Details:
Target Brand: {brand.name}
Official Brand URL: {brand.official_domains}
Phishing URL: {obfuscated_url}
Discovery Date: {incident.discovered_at or "Recent"}

Technical Evidence:
The domain {target_domain} is hosting a fraudulent website designed to steal sensitive user credentials by impersonating {brand.name}. We have collected forensic evidence, including full DOM snapshots and high-resolution screenshots, proving the malicious nature of this registration.

Requested Action:
We kindly request you to immediately suspend this domain to mitigate further harm to innocent users. Please acknowledge receipt of this report and inform us of the actions taken.

Regards,
Trusyn Brand Protection Team (on behalf of {brand.name})"""
        
        return {"subject": subject, "body": body, "recipient": registrar_email}

    def prepare_netcraft_style_report(self, incident: Incident, brand: Brand, origin_ip: str = "Unknown") -> Dict[str, str]:
        """Generates a detailed report similar to Netcraft/CleanUP standards."""
        target_domain = incident.target_url.split("//")[-1].split("/")[0]
        
        subject = f"Phishing Attack Notification - {target_domain} - {brand.name}"
        
        body = f"""Dear Sir or Madam,

You are currently hosting a phishing attack on your network at {origin_ip}:
{incident.target_url}

This attack targets our customer, {brand.name}, website URL {brand.official_domains}.

Please remove this fraudulent content, and any other associated fraudulent content, as soon as possible.

It is possible that this attack is being restricted so it is only visible from certain countries. Before deciding that the attack has been resolved please confirm it cannot be viewed from the following countries:
Turkey, Global

Additionally, please keep the fraudulent content safe so that our customer and law enforcement agencies can investigate this incident further once the site is offline.

Reporter: Trusyn Brand Protection
Issue Number: {str(incident.id)[:8]}

Regards,
Trusyn Brand Protection Team"""
        
        return {"subject": subject, "body": body, "recipient": "takedowns@netcraft.com"}

abuse_service = AbuseService()
