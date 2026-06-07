from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routes import auth, contacts, health, emergency, analytics, admin
from app.services.risk_analysis import load_models

logger = logging.getLogger(__name__)

# Modern FastAPI lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    try:
        from app.db.database import engine, Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Database startup error: {e}")
    try:
        load_models()
        logger.info("ML models loaded successfully.")
    except Exception as e:
        logger.error(f"ML model load error: {e}")
    yield
    # Shutdown actions (none needed)

app = FastAPI(
    title=settings.APP_NAME,
    description="Real-Time Health Monitoring & Emergency Alert API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
# Mobile clients from anywhere can access, restricted in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route attachments under '/api' prefix
app.include_router(auth.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(emergency.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
def read_root():
    """System status check."""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "docs_url": "/docs",
        "google_maps_enabled": settings.GOOGLE_MAPS_API_KEY is not None and settings.GOOGLE_MAPS_API_KEY != ""
    }
