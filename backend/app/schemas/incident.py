from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.models import IncidentStatus, ThreatType

# Shared properties
class IncidentBase(BaseModel):
    target_url: Optional[str] = None
    status: Optional[IncidentStatus] = IncidentStatus.DETECTED
    threat_type: Optional[ThreatType] = None
    confidence_score: Optional[float] = None

# Properties to receive via API on creation
class IncidentCreate(IncidentBase):
    target_url: str
    brand_id: UUID

# Properties to receive via API on update
class IncidentUpdate(IncidentBase):
    pass

class IncidentInDBBase(IncidentBase):
    id: Optional[UUID] = None
    brand_id: Optional[UUID] = None
    screenshot_path: Optional[str] = None
    discovered_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class Incident(IncidentInDBBase):
    pass
