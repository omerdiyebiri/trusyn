from playwright.async_api import async_playwright
import logging
import os
from datetime import datetime
from typing import Optional, Dict
import json

from app.services.screenshot_fallback_service import (
    attempt_fallback,
    is_block_page,
)


logger = logging.getLogger(__name__)


class ScreenshotService:
    def __init__(self, storage_path: str = "/app/storage/screenshots"):
        # Always absolute — same volume is mounted at /app/storage in backend,
        # worker, and ct_monitor containers. Relative paths would resolve
        # against the process cwd which can vary (esp. under Celery prefork).
        self.storage_path = os.path.abspath(storage_path)
        os.makedirs(self.storage_path, exist_ok=True)

    async def gather_evidence(self, url: str, incident_id: str) -> Dict[str, Optional[str]]:
        """
        Gather comprehensive evidence: Screenshot, DOM, and metadata.
        """
        evidence = {
            "screenshot_path": None,
            "dom_path": None,
            "page_title": None,
            "status_code": None,
            "screenshot_source": "playwright",
        }
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                    ],
                )
                # Pose as a Turkish-locale Android Chrome user — many phishing
                # kits gate on geo + UA + locale and serve a CF challenge to
                # everyone else. Mobile UA + tr-TR + Istanbul timezone +
                # geolocation is enough to defeat most JavaScript-based gates;
                # IP-level geo fences (only Turkish IPs allowed through) still
                # require a residential proxy in TR — separate decision.
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Linux; Android 14; SM-S921B) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/130.0.0.0 Mobile Safari/537.36"
                    ),
                    viewport={"width": 393, "height": 852},
                    device_scale_factor=2.625,
                    is_mobile=True,
                    has_touch=True,
                    locale="tr-TR",
                    timezone_id="Europe/Istanbul",
                    geolocation={"latitude": 41.0082, "longitude": 28.9784},
                    permissions=["geolocation"],
                    extra_http_headers={
                        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                        "Sec-Ch-Ua-Mobile": "?1",
                        "Sec-Ch-Ua-Platform": '"Android"',
                    },
                )

                # Stealth init script — patches the most common headless
                # detection signals (navigator.webdriver, missing chrome
                # runtime, languages, plugins). Real anti-bot vendors detect
                # more than this, but it clears the basic CF JS challenge.
                await context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                    "window.chrome = window.chrome || { runtime: {} };"
                    "Object.defineProperty(navigator, 'languages', "
                    "{get: () => ['tr-TR', 'tr', 'en']});"
                    "Object.defineProperty(navigator, 'plugins', "
                    "{get: () => [1,2,3,4,5]});"
                )

                page = await context.new_page()

                # 1. Navigate. Use 'domcontentloaded' (faster, less likely
                # to time out on heavy ad-laden phishing kits) then a small
                # network-idle wait to settle SPA hydration.
                response = await page.goto(url, timeout=60000,
                                           wait_until="domcontentloaded")
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                evidence["status_code"] = response.status if response else None
                evidence["page_title"] = await page.title()
                
                base_filename = f"{incident_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # 2. Take Screenshot
                screenshot_filename = f"{base_filename}.png"
                screenshot_path = os.path.join(self.storage_path, screenshot_filename)
                await page.screenshot(path=screenshot_path, full_page=True)
                evidence["screenshot_path"] = screenshot_path
                
                # 3. Capture DOM
                dom_content = await page.content()
                dom_filename = f"{base_filename}.html"
                dom_path = os.path.join(self.storage_path, dom_filename)
                with open(dom_path, "w", encoding="utf-8") as f:
                    f.write(dom_content)
                evidence["dom_path"] = dom_path

                await browser.close()

                # 4. If the captured page is a Cloudflare block, try the
                # fallback cascade (URLScan → PageSpeed Insights). They
                # render from different networks so CF rules tuned to drop
                # our IP often let them through. The fallback overwrites
                # the same file so downstream attachment / public-page
                # logic doesn't change.
                if is_block_page(dom_content, evidence.get("page_title") or ""):
                    logger.info("Block-page detected for %s; attempting "
                                "screenshot fallback", url)
                    fallback_path = await attempt_fallback(url, screenshot_path)
                    if fallback_path:
                        evidence["screenshot_source"] = "fallback"
                        logger.info("Fallback screenshot succeeded for %s", url)
                    else:
                        evidence["screenshot_source"] = "playwright_blocked"
                        logger.warning("All screenshot fallbacks failed "
                                       "for %s — block page persisted", url)

                return evidence
        except Exception as e:
            logger.error("Evidence gathering error for %s: %s", url, e)
            return evidence

    # Backward compatibility
    async def take_screenshot(self, url: str, incident_id: str) -> Optional[str]:
        res = await self.gather_evidence(url, incident_id)
        return res["screenshot_path"]

screenshot_service = ScreenshotService()
