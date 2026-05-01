from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.models import RecipientType, ReportStatus


class ReportBase(BaseModel):
    recipient_type: Optional[RecipientType] = None
    recipient_email: Optional[str] = None
    recipient_form_url: Optional[str] = None
    recipient_name: Optional[str] = None
    subject: Optional[str] = None
    message_id: Optional[str] = None
    status: Optional[ReportStatus] = None
    error_message: Optional[str] = None


class Report(ReportBase):
    id: UUID
    incident_id: UUID
    sent_at: Optional[datetime] = None
    raw_content: Optional[str] = None

    class Config:
        from_attributes = True
