import uuid
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import app.models.message
import app.models.website

class Chat_session(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False, index=True)

    messages = relationship("Message", back_populates='chat_session', cascade="all, delete-orphan")
    website = relationship("Website", back_populates='chat_sessions')


