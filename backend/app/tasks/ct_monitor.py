import certstream
import logging
import asyncio
import json
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.models import Brand, Incident, ThreatType, IncidentStatus
from app.tasks.scanner import analyze_incident_async
from app.services.typosquat_service import calculate_similarity

logger = logging.getLogger(__name__)

async def process_certstream_event(message, context):
    """
    Callback for each new certificate event from CertStream.
    """
    if message['message_type'] == "heartbeat":
        return

    all_domains = message['data']['leaf_cert']['all_domains']
    
    async with AsyncSessionLocal() as db:
        # Load all brands for matching
        result = await db.execute(select(Brand))
        brands = result.scalars().all()
        
        for domain in all_domains:
            # Skip wildcards
            if domain.startswith('*.'):
                domain = domain[2:]
            
            for brand in brands:
                # 1. Keyword Match
                keywords = [k.strip() for k in (brand.keywords or "").split(',') if k.strip()]
                matched_keyword = None
                for kw in keywords:
                    if kw.lower() in domain.lower():
                        matched_keyword = kw
                        break
                
                # 2. Typosquat Match (similarity check)
                is_typosquat = False
                if brand.official_domains:
                    official = brand.official_domains.split(',')[0].strip()
                    similarity = calculate_similarity(official, domain)
                    if similarity > 0.8:
                        is_typosquat = True

                if matched_keyword or is_typosquat:
                    # Check if incident already exists to avoid duplicates
                    existing = await db.execute(select(Incident).where(Incident.target_url == f"http://{domain}"))
                    if existing.scalars().first():
                        continue

                    logger.info(f"DETECTED THREAT: {domain} matches brand {brand.name}")
                    
                    new_incident = Incident(
                        brand_id=brand.id,
                        target_url=f"http://{domain}",
                        status=IncidentStatus.DETECTED,
                        threat_type=ThreatType.TYPOSQUATTING if is_typosquat else ThreatType.BRAND_IMPERSONATION,
                        confidence_score=0.9 if is_typosquat else 0.7
                    )
                    db.add(new_incident)
                    await db.commit()
                    await db.refresh(new_incident)
                    
                    # Trigger full analysis (screenshot, whois, etc.)
                    asyncio.create_task(analyze_incident_async(str(new_incident.id)))

def start_monitoring():
    """
    Starts the CertStream listener.
    Note: This is a blocking call, should run in its own process or thread.
    """
    logger.info("Starting CertStream monitoring...")
    certstream.listen_for_events(process_certstream_event, url='wss://certstream.calidog.io/')

if __name__ == "__main__":
    # For standalone testing
    logging.basicConfig(level=logging.INFO)
    start_monitoring()
