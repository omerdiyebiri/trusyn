import asyncio
import logging

from sqlalchemy.future import select

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.models import Brand, Incident, IncidentStatus, ThreatType
from app.services.screenshot_service import screenshot_service
from app.services.typosquat_service import calculate_similarity
from app.services.whois_service import whois_service


logger = logging.getLogger(__name__)

async def analyze_incident_async(incident_id: str):
    async with AsyncSessionLocal() as db:
        # Load incident with its brand
        result = await db.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        incident = result.scalars().first()
        if not incident:
            return

        result_brand = await db.execute(select(Brand).where(Brand.id == incident.brand_id))
        brand = result_brand.scalars().first()

        incident.status = IncidentStatus.ANALYZING
        await db.commit()

        # 1. Similarity / Typosquatting Check
        if brand and brand.official_domains:
            official_domain = brand.official_domains.split(',')[0] # Get first domain
            suspect_domain = incident.target_url.split("//")[-1].split("/")[0]
            
            similarity = calculate_similarity(official_domain, suspect_domain)
            incident.confidence_score = similarity
            
            if similarity > 0.8:
                incident.threat_type = ThreatType.TYPOSQUATTING
            else:
                incident.threat_type = ThreatType.BRAND_IMPERSONATION

        # 2. WHOIS Lookup
        domain = incident.target_url.split("//")[-1].split("/")[0]
        try:
            whois_info = whois_service.get_domain_info(domain)
            if whois_info:
                incident.whois_raw = str(whois_info)
        except Exception:
            pass

        # 3. Comprehensive Evidence Gathering (Screenshot, DOM, Title)
        try:
            evidence = await screenshot_service.gather_evidence(incident.target_url, str(incident.id))
            if evidence["screenshot_path"]:
                incident.screenshot_path = evidence["screenshot_path"]
            if evidence.get("screenshot_source"):
                incident.screenshot_source = evidence["screenshot_source"]
            
            # Log additional evidence for now (can be moved to DB columns later)
            if evidence["page_title"]:
                logger.info(f"Incident {incident_id} Page Title: {evidence['page_title']}")
            if evidence["dom_path"]:
                logger.info(f"Incident {incident_id} DOM saved to: {evidence['dom_path']}")
                
        except Exception as e:
            logger.error(f"Evidence gathering failed for {incident_id}: {e}")
        
        # Finalize
        incident.status = IncidentStatus.VALIDATED
        await db.commit()

@celery_app.task(name="app.tasks.scanner.analyze_incident")
def analyze_incident(incident_id: str):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # This is for environments where an event loop is already running
        asyncio.ensure_future(analyze_incident_async(incident_id))
    else:
        loop.run_until_complete(analyze_incident_async(incident_id))
