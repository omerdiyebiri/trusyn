from playwright.async_api import async_playwright
import os
from datetime import datetime
from typing import Optional, Dict
import json

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
            "status_code": None
        }
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Use a real-looking user agent to avoid bot detection
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # 1. Navigate
                response = await page.goto(url, timeout=60000, wait_until="networkidle")
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
                return evidence
        except Exception as e:
            print(f"Evidence gathering error for {url}: {e}")
            return evidence

    # Backward compatibility
    async def take_screenshot(self, url: str, incident_id: str) -> Optional[str]:
        res = await self.gather_evidence(url, incident_id)
        return res["screenshot_path"]

screenshot_service = ScreenshotService()
