"""
Cloudflare Abuse Reports API client.

Background (research summary, see docs/abuse-research/templates.md):
- abuse@cloudflare.com email is decorative — CF documents that they
  auto-bounce email submissions back to the abuse form. Engineering
  effort spent on the SMTP path is wasted.
- The web form (https://abuse.cloudflare.com/phishing) is Turnstile-
  protected; programmatic submission requires a captcha solver.
- The Abuse Reports REST API uses Bearer / Global-API-Key auth, no
  Turnstile, and feeds the SAME triage pipeline as the form. CF blog
  reports ~78% auto-resolve rate when the report matches their ML
  signal set (URL scanner verdict + DOM phishing markers + IOC feed
  citations).

This service:
- Submits phishing reports to /accounts/{id}/abuse-reports/abuse_phishing
- Pre-scans URLs through CF URL Scanner so the report lands on a URL
  CF's own scanner has already classified — material lift in auto-
  resolve probability.
- Supports both auth modes (auto-detected from configured creds).
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


CF_API_BASE = "https://api.cloudflare.com/client/v4"


def _auth_headers() -> Optional[Dict[str, str]]:
    """Build CF auth headers. Returns None if not configured."""
    if settings.CF_API_TOKEN:
        return {"Authorization": f"Bearer {settings.CF_API_TOKEN}"}
    if settings.CF_API_KEY and settings.CF_API_EMAIL:
        return {
            "X-Auth-Email": settings.CF_API_EMAIL,
            "X-Auth-Key": settings.CF_API_KEY,
        }
    # Heuristic: the legacy "cfk_..." prefix indicates a scoped token CF
    # generated through the dashboard's API-key-style flow; treat as Bearer.
    if settings.CF_API_KEY and settings.CF_API_KEY.startswith("cfk_"):
        return {"Authorization": f"Bearer {settings.CF_API_KEY}"}
    return None


def is_configured() -> bool:
    return bool(settings.CF_ACCOUNT_ID and _auth_headers())


def url_scanner_scan(target_url: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Submit URL to CF URL Scanner. Returns scan UUID; the result is
    polled separately. Used as a pre-flight before abuse report — if
    CF's own scanner has classified the URL as phishing by the time we
    submit the report, the report auto-resolves on the spot."""
    if not is_configured():
        return {"status": "skipped", "uuid": None,
                "error": "CF credentials not configured"}
    headers = _auth_headers() or {}
    headers["Content-Type"] = "application/json"
    url = (f"{CF_API_BASE}/accounts/{settings.CF_ACCOUNT_ID}"
           f"/urlscanner/v2/scan")
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                url,
                headers=headers,
                json={"url": target_url, "visibility": "public"},
            )
        if resp.status_code in (200, 201, 202):
            data = resp.json()
            return {
                "status": "submitted",
                "uuid": data.get("uuid") or (data.get("result", {}) or {}).get("uuid"),
                "error": None,
            }
        return {"status": "failed", "uuid": None,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        logger.warning("CF URL Scanner submit failed: %s", exc)
        return {"status": "failed", "uuid": None, "error": str(exc)}


def submit_phishing_report(
    *,
    target_urls: List[str],
    brand_name: str,
    justification: str,
    reporter_email: Optional[str] = None,
    reporter_name: Optional[str] = None,
    anonymize_to_host: bool = True,
    anonymize_to_owner: bool = True,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Submit a phishing abuse report to CF.

    Per CF API docs, the endpoint accepts up to 250 URLs per call but
    they MUST share the same hostname. Caller is responsible for
    grouping; this function will reject mixed-hostname batches with a
    short-circuit error.

    Returns: {status, report_id, error}
    """
    if not is_configured():
        return {"status": "skipped", "report_id": None,
                "error": "CF credentials not configured"}

    if not target_urls:
        return {"status": "skipped", "report_id": None,
                "error": "No URLs to report"}

    # Hostname-uniqueness gate
    from urllib.parse import urlparse
    hosts = {urlparse(u).hostname for u in target_urls}
    if len(hosts) > 1:
        return {"status": "rejected", "report_id": None,
                "error": f"Mixed hostnames in batch: {hosts}"}

    if len(target_urls) > 250:
        target_urls = target_urls[:250]

    email = reporter_email or settings.CF_API_EMAIL or "takedowns@trusyn.io"
    name = reporter_name or "Trusyn Brand Protection"

    payload: Dict[str, Any] = {
        "act": "abuse_phishing",
        "name": name,
        "email": email,
        "email2": email,
        "tele": "",
        "comments": justification[:5000],
        "urls": "\n".join(target_urls),
        "agent_name": name,
        "agent_email": email,
        "host_notification": "send-anon" if anonymize_to_host else "send",
        "owner_notification": "send-anon" if anonymize_to_owner else "send",
        "title": f"Phishing impersonating {brand_name}",
        "logoLink": "",
    }

    headers = _auth_headers() or {}
    headers["Content-Type"] = "application/json"
    url = (f"{CF_API_BASE}/accounts/{settings.CF_ACCOUNT_ID}"
           f"/abuse-reports/abuse_phishing")

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
        if resp.status_code in (200, 201, 202):
            data = resp.json()
            result = data.get("result") or {}
            report_id = (result.get("report_id") or result.get("id")
                         or data.get("messages", [{}])[0].get("ray_id"))
            return {
                "status": "submitted",
                "report_id": report_id,
                "raw": data,
                "error": None,
            }
        # CF returns specific error shapes — surface them for diagnosis
        try:
            err = resp.json()
        except Exception:
            err = {"_text": resp.text[:300]}
        logger.warning("CF abuse submit non-2xx (%s): %s",
                       resp.status_code, err)
        return {"status": "failed", "report_id": None,
                "error": f"HTTP {resp.status_code}: {str(err)[:300]}"}
    except Exception as exc:
        logger.error("CF abuse submit errored: %s", exc)
        return {"status": "failed", "report_id": None, "error": str(exc)}
