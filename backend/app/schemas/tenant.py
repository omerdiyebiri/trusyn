from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.models import SubscriptionPlan

# Shared properties
class TenantBase(BaseModel):
    name: Optional[str] = None
    subscription_plan: Optional[SubscriptionPlan] = SubscriptionPlan.BASIC

# Properties to receive via API on creation
class TenantCreate(TenantBase):
    name: str

# Properties to receive via API on update
class TenantUpdate(TenantBase):
    pass

class TenantInDBBase(TenantBase):
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class Tenant(TenantInDBBase):
    pass
