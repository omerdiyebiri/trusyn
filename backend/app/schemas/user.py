from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from app.models.models import UserRole

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = UserRole.TENANT_STAFF

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str
    tenant_id: UUID

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class User(UserInDBBase):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
