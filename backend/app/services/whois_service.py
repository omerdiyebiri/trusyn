import whois
from typing import Dict, Any, Optional

class WhoisService:
    @staticmethod
    def get_domain_info(domain: str) -> Optional[Dict[str, Any]]:
        try:
            w = whois.whois(domain)
            return {
                "domain_name": w.domain_name,
                "registrar": w.registrar,
                "whois_server": w.whois_server,
                "creation_date": w.creation_date,
                "expiration_date": w.expiration_date,
                "name_servers": w.name_servers,
                "status": w.status,
                "emails": w.emails,
                "org": w.org
            }
        except Exception as e:
            print(f"WHOIS error for {domain}: {e}")
            return None

whois_service = WhoisService()
