from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
import traceback

from app.core import security
from app.core.database import get_db
from app.models.models import Tenant, User, UserRole
from app.schemas.registration import RegisterTenant
from app.schemas.user import User as UserSchema

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserSchema)
async def register_tenant(
    *,
    db: AsyncSession = Depends(get_db),
    reg_in: RegisterTenant
) -> Any:
    """
    Register a new tenant and its first admin user.
    """
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == reg_in.admin_email))
        user_exists = result.scalars().first()
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        # Create Tenant
        new_tenant = Tenant(name=reg_in.tenant_name)
        db.add(new_tenant)
        await db.flush() # To get the tenant ID

        # Create Admin User
        new_user = User(
            email=reg_in.admin_email,
            password_hash=security.get_password_hash(reg_in.admin_password),
            tenant_id=new_tenant.id,
            role=UserRole.TENANT_ADMIN
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )
