"""Helpers to resolve a target domain's origin IP and detect Cloudflare proxying."""

import asyncio
import logging
import socket
from typing import List, Optional, Tuple

import httpx


logger = logging.getLogger(__name__)


CLOUDFLARE_ASNS = {"AS13335"}
CLOUDFLARE_NS_SUFFIXES = ("cloudflare.com", "ns.cloudflare.com")


async def resolve_a_records(domain: str) -> List[str]:
    """Return list of A records for domain. Empty list on failure."""
    try:
        loop = asyncio.get_event_loop()
        infos = await loop.getaddrinfo(domain, None, family=socket.AF_INET)
        return sorted({info[4][0] for info in infos})
    except Exception:
        return []


def is_cloudflare_ns(ns_records) -> bool:
    """Check if any NS record indicates Cloudflare."""
    if not ns_records:
        return False
    if isinstance(ns_records, str):
        ns_records = [ns_records]
    for ns in ns_records:
        if any(suf in ns.lower() for suf in CLOUDFLARE_NS_SUFFIXES):
            return True
    return False


async def discover_origin_ip(domain: str, ns_records=None) -> Optional[str]:
    """
    Best-effort origin-IP discovery. If domain is on Cloudflare, the resolved
    A records will be CF edge IPs (104.16.x.x / 104.18.x.x / 172.64–67.x.x etc.),
    which is NOT the origin. In that case we return None and rely on the operator
    or downstream hosting-provider report (sent via CF) to surface the origin.

    For non-CF domains, the first A record is the origin.
    """
    if is_cloudflare_ns(ns_records):
        return None
    a_records = await resolve_a_records(domain)
    return a_records[0] if a_records else None


def lookup_ip_org(ip: str, timeout: float = 6.0) -> Tuple[Optional[str], Optional[str]]:
    """
    Look up the organization behind an IP via RDAP (rdap.arin.net redirect chain).
    Returns (org_name, abuse_email). Either may be None.

    Used to populate hosting abuse channel when domain WHOIS lacks .org info
    (very common with privacy-protected domain registrations).
    """
    if not ip:
        return None, None
    url = f"https://rdap.org/ip/{ip}"
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True,
                          headers={"User-Agent": "Trusyn/1.0 (abuse research)"}) as client:
            resp = client.get(url)
        if resp.status_code != 200:
            return None, None
        rdap = resp.json()
    except Exception as exc:
        logger.warning("IP RDAP fetch failed for %s: %s", ip, exc)
        return None, None

    org_name: Optional[str] = rdap.get("name")
    abuse_email: Optional[str] = None

    def walk(entity: dict, in_abuse: bool = False) -> None:
        nonlocal org_name, abuse_email
        roles = [r.lower() for r in entity.get("roles", [])]
        is_abuse = in_abuse or "abuse" in roles
        vcard = entity.get("vcardArray")
        if isinstance(vcard, list) and len(vcard) > 1:
            for item in vcard[1]:
                if not isinstance(item, list) or len(item) < 4:
                    continue
                if item[0] == "fn" and not org_name:
                    org_name = item[3]
                if item[0] == "email" and is_abuse and not abuse_email:
                    addr = item[3]
                    if isinstance(addr, str):
                        abuse_email = addr
        for sub in entity.get("entities", []) or []:
            walk(sub, is_abuse)

    for ent in rdap.get("entities", []) or []:
        walk(ent)

    return org_name, abuse_email
