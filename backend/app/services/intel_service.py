"""
Submissions to external threat-intel platforms.

Each submitter:
  - returns a dict with `status`, `public_url`, `error`
  - is non-fatal: failures are reported to caller, not raised, so the rest of
    the dispatch pipeline continues even if a single intel platform is down.

Implemented:
  - URLScan.io   POST /api/v1/scan/   (header API-Key)
  - abuse.ch ThreatFox  POST /api/v1/   (header Auth-Key)

Microsoft SmartScreen is form-only (no public API for submission); the
audit row is rendered as form_only by abuse_service.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


def submit_urlscan(target_url: str, brand_tag: Optional[str] = None,
                   timeout: float = 15.0) -> Dict[str, Any]:
    """Submit URL to URLScan.io for public scanning. Free tier requires
    API-Key. Returns the public result URL on success."""
    if not settings.URLSCAN_API_KEY:
        return {"status": "skipped", "public_url": None,
                "error": "URLSCAN_API_KEY not configured"}

    payload: Dict[str, Any] = {
        "url": target_url,
        "visibility": settings.URLSCAN_VISIBILITY,
    }
    if brand_tag:
        payload["tags"] = [f"trusyn-brand:{brand_tag}"[:80], "phishing"]

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                "https://urlscan.io/api/v1/scan/",
                headers={
                    "Content-Type": "application/json",
                    "API-Key": settings.URLSCAN_API_KEY,
                    "User-Agent": "Trusyn/1.0",
                },
                json=payload,
            )
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"status": "submitted",
                    "public_url": data.get("result"),
                    "uuid": data.get("uuid"),
                    "error": None}
        if resp.status_code == 400:
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            return {"status": "rejected", "public_url": None,
                    "error": data.get("description") or resp.text[:200]}
        if resp.status_code == 429:
            return {"status": "rate_limited", "public_url": None,
                    "error": "URLScan rate limit hit"}
        return {"status": "failed", "public_url": None,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        logger.warning("URLScan submission failed: %s", exc)
        return {"status": "failed", "public_url": None, "error": str(exc)}


def submit_threatfox(target_url: str, brand_tag: Optional[str] = None,
                     timeout: float = 15.0) -> Dict[str, Any]:
    """Submit phishing IOC to abuse.ch ThreatFox. Auth-Key required (free)."""
    if not settings.ABUSE_CH_AUTH_KEY:
        return {"status": "skipped", "public_url": None,
                "error": "ABUSE_CH_AUTH_KEY not configured"}

    tags = ["phishing"]
    if brand_tag:
        tags.append(f"brand-{brand_tag}".replace(" ", "-")[:40])

    payload: Dict[str, Any] = {
        "query": "submit_ioc",
        "threat_type": "payload_delivery",
        "ioc_type": "url",
        "malware": "Phishing",
        "confidence_level": 90,
        "iocs": [{
            "ioc_value": target_url,
            "tags": tags,
            "anonymous": "0",
        }],
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                "https://threatfox-api.abuse.ch/api/v1/",
                headers={
                    "Auth-Key": settings.ABUSE_CH_AUTH_KEY,
                    "Content-Type": "application/json",
                    "User-Agent": "Trusyn/1.0",
                },
                json=payload,
            )
        if resp.status_code != 200:
            return {"status": "failed", "public_url": None,
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        if data.get("query_status") == "ok":
            iocs = data.get("data", {}).get("ok") or []
            if iocs:
                ioc = iocs[0]
                ioc_id = ioc.get("id") or ioc.get("ioc_id")
                public_url = (f"https://threatfox.abuse.ch/ioc/{ioc_id}/"
                              if ioc_id else None)
                return {"status": "submitted", "public_url": public_url,
                        "uuid": ioc_id, "error": None}
            return {"status": "submitted", "public_url": None,
                    "uuid": None, "error": None}

        return {"status": "rejected", "public_url": None,
                "error": data.get("query_status") or "ThreatFox rejected submission"}
    except Exception as exc:
        logger.warning("ThreatFox submission failed: %s", exc)
        return {"status": "failed", "public_url": None, "error": str(exc)}
