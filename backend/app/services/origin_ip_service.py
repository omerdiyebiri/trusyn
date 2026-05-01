"""Helpers to resolve a target domain's origin IP and detect Cloudflare proxying."""

import asyncio
import socket
from typing import List, Optional


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
