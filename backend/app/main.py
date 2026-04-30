from fastapi import FastAPI
from app.api.api_v1.api import api_router

app = FastAPI(
    title="Trusyn Brand Protection API",
    description="Automated phishing detection and abuse reporting system.",
    version="0.1.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Trusyn API"}
