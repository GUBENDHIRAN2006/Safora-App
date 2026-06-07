from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Setup SQLAlchemy engine
# pool_pre_ping=True enables checking the connection health on each checkout
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
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
