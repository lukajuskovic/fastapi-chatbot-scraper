import os
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import get_settings

settings = get_settings()

DB_URL = os.getenv("DB_URL",
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@localhost:5432/{settings.DB_NAME}")

SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL")

Base = declarative_base()
