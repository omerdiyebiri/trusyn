from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.models import Incident, Brand, Report, ReportStatus, RecipientType
from app.services.abuse_service import abuse_service
import asyncio
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import ast

async def send_abuse_reports_async(incident_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Incident)
            .options(selectinload(Incident.brand))
            .where(Incident.id == incident_id)
        )
        incident = result.scalars().first()
        if not incident or not incident.whois_raw:
            return

        whois_data = ast.literal_eval(incident.whois_raw)
        
        # 1. Check Cloudflare
        if abuse_service.is_cloudflare(whois_data):
            report_data = abuse_service.prepare_cloudflare_report(incident, incident.brand)
            new_report = Report(
                incident_id=incident.id,
                recipient_type=RecipientType.CLOUDFLARE,
                recipient_email=report_data["recipient"],
                raw_content=report_data["body"],
                status=ReportStatus.SENT
            )
            db.add(new_report)
            # Logic to actually send email via SMTP would go here
        
        # 2. Hosting Report
        abuse_email = abuse_service.find_abuse_email(whois_data)
        if abuse_email:
            report_data = abuse_service.prepare_hosting_report(incident, incident.brand, abuse_email)
            new_report = Report(
                incident_id=incident.id,
                recipient_type=RecipientType.HOSTING,
                recipient_email=report_data["recipient"],
                raw_content=report_data["body"],
                status=ReportStatus.SENT
            )
            db.add(new_report)
            # Logic to actually send email via SMTP would go here
        
        await db.commit()

@celery_app.task(name="app.tasks.reporter.send_abuse_reports")
def send_abuse_reports(incident_id: str):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(send_abuse_reports_async(incident_id))
    else:
        loop.run_until_complete(send_abuse_reports_async(incident_id))
