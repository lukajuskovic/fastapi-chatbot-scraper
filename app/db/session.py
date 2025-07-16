from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import DB_URL, SYNC_DATABASE_URL

async_engine = create_async_engine(
    DB_URL,
    echo=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_timeout=30
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)



#For scraper, needs to be changed

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
    pool_timeout=30
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)