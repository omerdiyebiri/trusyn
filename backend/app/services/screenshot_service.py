from playwright.async_api import async_playwright
import os
from datetime import datetime
from typing import Optional

class ScreenshotService:
    def __init__(self, storage_path: str = "storage/screenshots"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)

    async def take_screenshot(self, url: str, incident_id: str) -> Optional[str]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                # Set a reasonable timeout
                await page.goto(url, timeout=60000, wait_until="networkidle")
                
                filename = f"{incident_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = os.path.join(self.storage_path, filename)
                
                await page.screenshot(path=filepath, full_page=True)
                await browser.close()
                return filepath
        except Exception as e:
            print(f"Screenshot error for {url}: {e}")
            return None

screenshot_service = ScreenshotService()
