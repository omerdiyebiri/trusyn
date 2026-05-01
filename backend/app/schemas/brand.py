from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

# Shared properties
class BrandBase(BaseModel):
    name: Optional[str] = None
    official_domains: Optional[str] = None
    keywords: Optional[str] = None
    logo_url: Optional[str] = None
    country_restrictions: Optional[str] = None

# Properties to receive via API on creation
class BrandCreate(BrandBase):
    name: str

# Properties to receive via API on update
class BrandUpdate(BrandBase):
    pass

class BrandInDBBase(BrandBase):
    id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    vekalet_status: Optional[str] = None
    vekalet_uploaded_at: Optional[datetime] = None
    vekalet_reviewed_at: Optional[datetime] = None
    vekalet_reject_reason: Optional[str] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class Brand(BrandInDBBase):
    pass
