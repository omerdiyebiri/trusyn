from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, registration, brands, incidents

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(registration.router, tags=["registration"])
api_router.include_router(brands.router, prefix="/brands", tags=["brands"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
