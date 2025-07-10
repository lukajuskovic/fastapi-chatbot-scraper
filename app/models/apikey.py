import uuid
from sqlalchemy import Column, String, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from datetime import datetime
import app.models.user
import app.models.website

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