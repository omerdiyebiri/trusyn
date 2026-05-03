"""
Screenshot fallback cascade for sites that block our Playwright probe.

Cloudflare's managed challenge ("Sorry, you have been blocked", Ray ID
visible) often returns 200 with a tiny HTML body and no real content.
Our Turkish-mobile profile defeats most JS gates but not IP-level fences
or strict bot-fight rules. When that happens, the captured screenshot is
useless to a registrar reviewer.

This module renders the page from someone else's network when ours is
blocked. Cascade:

  1. URLScan.io — submit a fresh public scan, poll the screenshots/{uuid}
     endpoint until ready (~30-60s typical). URLScan runs from US/EU
     residential and datacenter pools; CF rules tuned to drop our IP
     often let URLScan through.

  2. Google PageSpeed Insights — Lighthouse audit returns a base64 PNG
     in `lighthouseResult.audits.final-screenshot.details.data`. Fetched
     from Google's network, which CF treats as well-known crawler IPs;
     bypass rate is ~50-70% in practice.

Both fallbacks overwrite the original screenshot path so the rest of the
pipeline (mail attachment, public incident page) sees a valid PNG without
any extra plumbing.
"""

import asyncio
import base64
import logging
import time
from typing import Optional

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


# String markers we treat as a CF / generic-block landing page. Case-folded.
CF_BLOCK_MARKERS = (
    "cf-error-details",
    "sorry, you have been blocked",
    "why have i been blocked",
    "cloudflare ray id",
    "performance & security by cloudflare",
    "attention required! | cloudflare",
    "checking your browser before accessing",
    "just a moment...",  # CF Turnstile interstitial
)


def is_block_page(html: str, title: str = "") -> bool:
    """Heuristic detector for Cloudflare-style block / challenge pages.
    True positives outweigh false positives in our context — a phishing
    site's real content rarely matches these markers, and treating an
    edge case as blocked just triggers a (cheap) fallback scan."""
    if not html and not title:
        return False
    blob = (html + " " + (title or "")).lower()
    return any(m in blob for m in CF_BLOCK_MARKERS)


async def _fetch_urlscan_screenshot(target_url: str, save_path: str,
                                    poll_timeout_s: int = 90) -> Optional[str]:
    """Submit fresh URLScan, poll for screenshot, write PNG to save_path."""
    if not settings.URLSCAN_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            sub = await client.post(
                "https://urlscan.io/api/v1/scan/",
                headers={
                    "API-Key": settings.URLSCAN_API_KEY,
                    "Content-Type": "application/json",
                    "User-Agent": "Trusyn/1.0",
                },
                json={"url": target_url,
                      "visibility": settings.URLSCAN_VISIBILITY or "public"},
            )
            if sub.status_code not in (200, 201):
                logger.info("URLScan submit failed for fallback: HTTP %s",
                            sub.status_code)
                return None
            scan_uuid = sub.json().get("uuid")
            if not scan_uuid:
                return None
            screenshot_url = f"https://urlscan.io/screenshots/{scan_uuid}.png"
            deadline = time.time() + poll_timeout_s
            # First-attempt 404 is normal — scan still rendering.
            await asyncio.sleep(20)
            while time.time() < deadline:
                resp = await client.get(screenshot_url)
                if resp.status_code == 200 and len(resp.content) > 1024:
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                    logger.info("URLScan fallback screenshot saved (%d bytes)",
                                len(resp.content))
                    return save_path
                await asyncio.sleep(5)
            logger.info("URLScan fallback timed out after %ds", poll_timeout_s)
            return None
    except Exception as exc:
        logger.warning("URLScan fallback errored: %s", exc)
        return None


async def _fetch_pagespeed_screenshot(target_url: str,
                                      save_path: str) -> Optional[str]:
    """PageSpeed Insights returns a Lighthouse final-screenshot as a
    base64 PNG data URI. Free tier works without a key but at low rate."""
    base = ("https://pagespeedonline.googleapis.com/pagespeedonline/"
            "v5/runPagespeed")
    params = {"url": target_url, "strategy": "mobile",
              "category": "performance"}
    if settings.GOOGLE_PAGESPEED_API_KEY:
        params["key"] = settings.GOOGLE_PAGESPEED_API_KEY
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.get(base, params=params)
            if r.status_code != 200:
                logger.info("PageSpeed fallback failed: HTTP %s", r.status_code)
                return None
            audits = (r.json().get("lighthouseResult", {})
                      .get("audits", {}))
            # Try final-screenshot first (the actual page), fall back to
            # full-page-screenshot if Lighthouse only produced that.
            data_uri = None
            ss = audits.get("final-screenshot", {})
            details = ss.get("details", {}) or {}
            data_uri = details.get("data")
            if not data_uri:
                fp = audits.get("full-page-screenshot", {}) \
                    .get("details", {}) or {}
                data_uri = (fp.get("screenshot") or {}).get("data")
            if not data_uri or "," not in data_uri:
                return None
            png_bytes = base64.b64decode(data_uri.split(",", 1)[1])
            if len(png_bytes) < 1024:
                return None
            with open(save_path, "wb") as f:
                f.write(png_bytes)
            logger.info("PageSpeed fallback screenshot saved (%d bytes)",
                        len(png_bytes))
            return save_path
    except Exception as exc:
        logger.warning("PageSpeed fallback errored: %s", exc)
        return None


async def attempt_fallback(target_url: str, save_path: str) -> Optional[str]:
    """Try URLScan first, then PageSpeed. Returns the path on success
    so callers can flag the screenshot as 'sourced via fallback'."""
    p = await _fetch_urlscan_screenshot(target_url, save_path)
    if p:
        return p
    return await _fetch_pagespeed_screenshot(target_url, save_path)
