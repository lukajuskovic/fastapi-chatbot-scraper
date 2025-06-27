import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, func, Text
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum
import app.models.user

class ScrapingStatus(enum.Enum):
    PENDING = "PENDING"
    SCRAPING = "SCRAPING"
    COMPLETED = "COMPLETED"

class MessageSender(enum.Enum):
    USER = "user"
    BOT = "bot"

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True)

    sender = Column(Enum(MessageSender), nullable=False)
    text = Column(Text, nullable=False)
    time_created = Column(DateTime(timezone=True), server_default=func.now())

    chat_session = relationship("Chat_session", back_populates='messages')


class Chat_session(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False, index=True)

    messages = relationship("Message", back_populates='chat_session', cascade="all, delete-orphan")
    website = relationship("Website", back_populates='chat_sessions')


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False, unique=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scraping_status = Column(Enum(ScrapingStatus), nullable=False, default=ScrapingStatus.PENDING)

    owner = relationship("User", back_populates= "websites")
    chat_sessions = relationship("Chat_session", back_populates='website', cascade="all, delete-orphan")
    scraped_content = relationship("ScrapedContent", back_populates="website", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="website", cascade="all, delete-orphan")


class ScrapedContent(Base):
    __tablename__ = "scraped_content"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False, index=True)
    text_content = Column(Text, nullable=False)
    source_url = Column(String(2048))
    image_url = Column(String(2048), nullable=True)
    embedding = Column(Vector(384), nullable=True)

    website = relationship("Website", back_populates="scraped_content")