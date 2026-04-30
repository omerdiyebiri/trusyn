from fastapi import FastAPI
from app.api.api_v1.api import api_router
from app.core.database import engine, Base

app = FastAPI(
    title="Trusyn Brand Protection API",
    description="Automated phishing detection and abuse reporting system.",
    version="0.1.0"
)

@app.on_event("startup")
async def init_tables():
    async with engine.begin() as conn:
        # Warning: For production, use Alembic migrations instead of create_all
        await conn.run_sync(Base.metadata.create_all)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Trusyn API"}
