from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.models import Tenant, User
from app.schemas.user import Token, User as UserSchema

router = APIRouter()


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=200)

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserSchema)
async def read_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Return the authenticated user's profile (id, email, role, tenant_id)."""
    return current_user


@router.get("/me/tenant")
async def read_my_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Return the tenant the authenticated user belongs to."""
    if not current_user.tenant_id:
        return None
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalars().first()
    if not tenant:
        return None
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "subscription_plan": (tenant.subscription_plan.value
                              if tenant.subscription_plan else None),
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
    }


@router.post("/me/password")
async def change_password(
    *,
    payload: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Change the authenticated user's password."""
    if not security.verify_password(
        payload.current_password, current_user.password_hash
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400,
                            detail="New password must differ from the current one")
    current_user.password_hash = security.get_password_hash(payload.new_password)
    db.add(current_user)
    await db.commit()
    return {"status": "ok"}
