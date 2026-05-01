"""
Domain registration intel.

Two backends are tried in order:
  1. RDAP (https://rdap.org/domain/<name>) — modern HTTP/JSON, IANA-coordinated,
     covers all gTLDs and most ccTLDs reliably. Preferred.
  2. python-whois — legacy, regex-based parser of registry whois ports. Falls
     short on `.online`, `.io`, many ccTLDs. Used only as a last resort.

Output is normalized to the same dict shape regardless of backend so downstream
code (reporter, takedown_tracker) can rely on consistent fields.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
import whois as pywhois


logger = logging.getLogger(__name__)


def _extract_rdap_emails(rdap: dict) -> List[str]:
    """Walk the RDAP `entities` graph and collect every email vCard found.
    Abuse-role entities first, then the rest."""
    abuse_emails: List[str] = []
    other_emails: List[str] = []

    def walk(entity: dict, in_abuse: bool = False) -> None:
        roles = [r.lower() for r in entity.get("roles", [])]
        is_abuse = in_abuse or "abuse" in roles
        vcard = entity.get("vcardArray")
        if isinstance(vcard, list) and len(vcard) > 1:
            for item in vcard[1]:
                if isinstance(item, list) and len(item) >= 4 and item[0] == "email":
                    addr = item[3]
                    if isinstance(addr, str) and addr:
                        (abuse_emails if is_abuse else other_emails).append(addr)
        for sub in entity.get("entities", []) or []:
            walk(sub, is_abuse)

    for ent in rdap.get("entities", []) or []:
        walk(ent)

    seen = set()
    out = []
    for e in abuse_emails + other_emails:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def _extract_rdap_registrar(rdap: dict) -> Optional[str]:
    """Find the registrar entity name from RDAP."""
    for ent in rdap.get("entities", []) or []:
        roles = [r.lower() for r in ent.get("roles", [])]
        if "registrar" in roles:
            vcard = ent.get("vcardArray")
            if isinstance(vcard, list) and len(vcard) > 1:
                for item in vcard[1]:
                    if isinstance(item, list) and len(item) >= 4 and item[0] == "fn":
                        return item[3]
            handle = ent.get("handle")
            if handle:
                return handle
    return None


def _extract_rdap_event(rdap: dict, action: str) -> Optional[str]:
    for ev in rdap.get("events", []) or []:
        if ev.get("eventAction") == action:
            return ev.get("eventDate")
    return None


def _extract_rdap_nameservers(rdap: dict) -> List[str]:
    out = []
    for ns in rdap.get("nameservers", []) or []:
        ldh = ns.get("ldhName") or ns.get("unicodeName")
        if ldh:
            out.append(ldh)
    return out


def _via_rdap(domain: str, timeout: float = 8.0) -> Optional[Dict[str, Any]]:
    """Query rdap.org (which redirects to the authoritative RDAP server)."""
    url = f"https://rdap.org/domain/{domain}"
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True,
                          headers={"User-Agent": "Trusyn/1.0 (abuse research)"}) as client:
            resp = client.get(url)
        if resp.status_code != 200:
            logger.info("RDAP non-200 for %s: %s", domain, resp.status_code)
            return None
        rdap = resp.json()
    except Exception as exc:
        logger.warning("RDAP fetch failed for %s: %s", domain, exc)
        return None

    return {
        "domain_name": rdap.get("ldhName") or domain,
        "registrar": _extract_rdap_registrar(rdap),
        "creation_date": _extract_rdap_event(rdap, "registration"),
        "expiration_date": _extract_rdap_event(rdap, "expiration"),
        "name_servers": _extract_rdap_nameservers(rdap),
        "status": rdap.get("status"),
        "emails": _extract_rdap_emails(rdap),
        "org": _extract_rdap_registrar(rdap),
        "_source": "rdap",
    }


def _via_pywhois(domain: str) -> Optional[Dict[str, Any]]:
    try:
        w = pywhois.whois(domain)
    except Exception as exc:
        logger.warning("pywhois failed for %s: %s", domain, exc)
        return None
    if not w or not getattr(w, "registrar", None):
        return None
    return {
        "domain_name": w.domain_name,
        "registrar": w.registrar,
        "whois_server": w.whois_server,
        "creation_date": w.creation_date,
        "expiration_date": w.expiration_date,
        "name_servers": w.name_servers,
        "status": w.status,
        "emails": w.emails,
        "org": w.org,
        "_source": "pywhois",
    }


class WhoisService:
    @staticmethod
    def get_domain_info(domain: str) -> Optional[Dict[str, Any]]:
        if not domain:
            return None
        return _via_rdap(domain) or _via_pywhois(domain)


whois_service = WhoisService()
