from pydantic import BaseModel, EmailStr

class RegisterTenant(BaseModel):
    tenant_name: str
    admin_email: EmailStr
    admin_password: str
