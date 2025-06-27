import uuid

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class User(Base):
    __tablename__="users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email=Column(String,unique=True,index=True,nullable=False)
    username=Column(String,unique=True,index=True,nullable=False)
    hashed_password=Column(String,nullable=False)

    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    websites = relationship( "Website", back_populates="owner", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hashed_key = Column(String(255), nullable=False, unique=True)
    prefix = Column(String(8), nullable=False, unique=True) # For quick lookups
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    is_active = Column(Boolean, default=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    user = relationship("User", back_populates="api_keys")
    website = relationship("Website", back_populates="api_keys")
