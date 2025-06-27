from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .base import DB_URL

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
