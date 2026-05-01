from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from app.api.api_v1.api import api_router
from app.core.database import engine, Base
from app.core.migrations import run_idempotent_migrations

# Setup basic logging to file
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trusyn Brand Protection API",
    description="Automated phishing detection and abuse reporting system.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def init_tables():
    from app.core.database import AsyncSessionLocal
    from app.models.models import User, Tenant, UserRole
    from app.core import security
    from sqlalchemy.future import select

    retries = 5
    while retries > 0:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully.")
            await run_idempotent_migrations(engine)
            
            # Create a test admin user if none exists
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.email == "admin@trusyn.io"))
                admin = result.scalars().first()
                if not admin:
                    new_tenant = Tenant(name="Default Tenant")
                    db.add(new_tenant)
                    await db.flush()
                    
                    new_user = User(
                        email="admin@trusyn.io",
                        password_hash=security.get_password_hash("password123"),
                        tenant_id=new_tenant.id,
                        role=UserRole.TENANT_ADMIN
                    )
                    db.add(new_user)
                    await db.commit()
                    logger.info("Test admin user created: admin@trusyn.io / password123")
            break
        except Exception as e:
            logger.error(f"Error during startup: {e}", exc_info=True)
            retries -= 1
            await asyncio.sleep(2)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Trusyn API"}

@app.get("/logs")
async def get_logs():
    try:
        with open("app.log", "r") as f:
            return {"logs": f.read()}
    except Exception as e:
        return {"error": str(e)}
