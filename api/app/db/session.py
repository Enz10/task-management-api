from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Ensure DATABASE_URL is available
if settings.DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not configured properly.")

connect_args = {} # Add specific arguments if needed for PostgreSQL

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
