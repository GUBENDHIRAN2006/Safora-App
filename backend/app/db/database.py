from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Validate DATABASE_URL is set
if not settings.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Please configure it in your .env file or Render environment variables."
    )

# Build connect_args for SSL (required for Supabase / cloud Postgres)
connect_args = {}
db_url = settings.DATABASE_URL

# Supabase requires SSL - add sslmode=require if not already in the URL
if "supabase.co" in db_url and "sslmode" not in db_url:
    connect_args = {"sslmode": "require"}
    logger.info("Supabase detected - enabling SSL mode for database connection.")

# Setup SQLAlchemy engine
# pool_pre_ping=True enables checking the connection health on each checkout
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args
)

# Setup session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup declarative base
Base = declarative_base()

def get_db():
    """Dependency generator for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

