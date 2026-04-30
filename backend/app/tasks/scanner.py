from app.core.celery_app import celery_app
from app.services.whois_service import whois_service
from app.services.screenshot_service import screenshot_service
from app.core.database import AsyncSessionLocal
from app.models.models import Incident, IncidentStatus
import asyncio
from sqlalchemy.future import select

async def analyze_incident_async(incident_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = result.scalars().first()
        if not incident:
            return

        incident.status = IncidentStatus.ANALYZING
        await db.commit()

        # 1. WHOIS Lookup
        domain = incident.target_url.split("//")[-1].split("/")[0]
        whois_info = whois_service.get_domain_info(domain)
        if whois_info:
            incident.whois_raw = str(whois_info)

        # 2. Screenshot
        screenshot_path = await screenshot_service.take_screenshot(incident.target_url, str(incident.id))
        if screenshot_path:
            incident.screenshot_path = screenshot_path
        
        # 3. Validation Logic (Simplified for now)
        # In a real scenario, compare with brand logo/keywords here
        incident.status = IncidentStatus.VALIDATED
        incident.confidence_score = 0.85 # Mock score
        
        await db.commit()

@celery_app.task(name="app.tasks.scanner.analyze_incident")
def analyze_incident(incident_id: str):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # This is for environments where an event loop is already running
        asyncio.ensure_future(analyze_incident_async(incident_id))
    else:
        loop.run_until_complete(analyze_incident_async(incident_id))
