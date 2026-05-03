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
from typing import Any, Dict, List, Optional  # noqa: F401

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


CF_API_BASE = "https://api.cloudflare.com/client/v4"


def _auth_header_candidates() -> List[Dict[str, str]]:
    """Return all configured auth header sets to try, in order.
    Auth-method observations from production diagnostics:
      - `cfk_`-prefixed keys are CF's Global API Key on migrated
        accounts. They authenticate via legacy X-Auth-Email +
        X-Auth-Key headers (NOT Bearer — Bearer returns 9109
        'Invalid access token').
      - Modern scoped tokens (created via "Create Token" UI, no
        cfk_ prefix) authenticate via Bearer.
    We try the explicit token first, then the keypair, then a
    speculative Bearer attempt with the key as a last resort."""
    out: List[Dict[str, str]] = []
    if settings.CF_API_TOKEN:
        out.append({"Authorization": f"Bearer {settings.CF_API_TOKEN}"})
    if settings.CF_API_KEY and settings.CF_API_EMAIL:
        out.append({
            "X-Auth-Email": settings.CF_API_EMAIL,
            "X-Auth-Key": settings.CF_API_KEY,
        })
    # Speculative Bearer attempt for keys without an associated email
    # (e.g. operator pasted a scoped token into CF_API_KEY).
    if settings.CF_API_KEY and not settings.CF_API_EMAIL:
        out.append({"Authorization": f"Bearer {settings.CF_API_KEY}"})
    return out


def _auth_headers() -> Optional[Dict[str, str]]:
    """Backward-compat helper: returns the first candidate, or None."""
    cands = _auth_header_candidates()
    return cands[0] if cands else None


def is_configured() -> bool:
    return bool(settings.CF_ACCOUNT_ID and _auth_header_candidates())


def _try_request(method: str, url: str, *, json_body: Optional[dict] = None,
                 timeout: float = 30.0) -> Any:
    """Attempt the request with each configured auth header set; return the
    first response that isn't 401/403. If every candidate auth-fails, the
    final response is returned so the caller can surface the error."""
    last_resp = None
    for headers in _auth_header_candidates():
        h = dict(headers)
        if json_body is not None:
            h["Content-Type"] = "application/json"
        with httpx.Client(timeout=timeout) as client:
            resp = client.request(method, url, headers=h, json=json_body)
        last_resp = resp
        if resp.status_code not in (401, 403):
            return resp
    return last_resp


def url_scanner_scan(target_url: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Submit URL to CF URL Scanner. Returns scan UUID; the result is
    polled separately. Used as a pre-flight before abuse report — if
    CF's own scanner has classified the URL as phishing by the time we
    submit the report, the report auto-resolves on the spot."""
    if not is_configured():
        return {"status": "skipped", "uuid": None,
                "error": "CF credentials not configured"}
    url = (f"{CF_API_BASE}/accounts/{settings.CF_ACCOUNT_ID}"
           f"/urlscanner/v2/scan")
    try:
        resp = _try_request("POST", url,
                            json_body={"url": target_url, "visibility": "public"},
                            timeout=timeout)
        if resp is None:
            return {"status": "failed", "uuid": None,
                    "error": "No auth candidate available"}
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

    # Reporter email is independent of CF_API_EMAIL (which is the login
    # email used for auth). Prefer CF_REPORTER_EMAIL → operational
    # takedowns mailbox (EMAILS_FROM_EMAIL) → caller-supplied → finally
    # CF_API_EMAIL as last resort.
    email = (reporter_email
             or settings.CF_REPORTER_EMAIL
             or settings.EMAILS_FROM_EMAIL
             or settings.CF_API_EMAIL
             or "takedowns@trusyn.io")
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

    url = (f"{CF_API_BASE}/accounts/{settings.CF_ACCOUNT_ID}"
           f"/abuse-reports/abuse_phishing")

    try:
        resp = _try_request("POST", url, json_body=payload, timeout=timeout)
        if resp is None:
            return {"status": "failed", "report_id": None,
                    "error": "No auth candidate available"}
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


def verify_credentials() -> Dict[str, Any]:
    """Sanity check: hit /user (Bearer) and /accounts/{id} for each
    configured auth header set, report which pass. Used by an admin
    diagnostic endpoint so we can tell the operator exactly which auth
    method works for their key without firing a real abuse report."""
    if not settings.CF_ACCOUNT_ID:
        return {"ok": False, "error": "CF_ACCOUNT_ID not set"}
    candidates = _auth_header_candidates()
    if not candidates:
        return {"ok": False, "error": "No CF_API_KEY/CF_API_TOKEN configured"}
    results = []
    user_url = f"{CF_API_BASE}/user"
    accounts_url = f"{CF_API_BASE}/accounts/{settings.CF_ACCOUNT_ID}"
    for idx, headers in enumerate(candidates):
        method_label = ("bearer" if "Authorization" in headers else "legacy_keypair")
        try:
            with httpx.Client(timeout=15.0) as client:
                u = client.get(user_url, headers=headers)
                a = client.get(accounts_url, headers=headers)
            results.append({
                "auth_method": method_label,
                "user_status": u.status_code,
                "account_status": a.status_code,
                "user_ok": u.status_code == 200,
                "account_ok": a.status_code == 200,
                "account_error": (None if a.status_code == 200
                                  else a.text[:300]),
            })
        except Exception as exc:
            results.append({
                "auth_method": method_label,
                "error": str(exc),
            })
    any_ok = any(r.get("account_ok") for r in results)
    return {"ok": any_ok, "candidates": results,
            "account_id": settings.CF_ACCOUNT_ID,
            "email_set": bool(settings.CF_API_EMAIL),
            "key_prefix": (settings.CF_API_KEY[:5] if settings.CF_API_KEY else None),
            "token_set": bool(settings.CF_API_TOKEN)}
