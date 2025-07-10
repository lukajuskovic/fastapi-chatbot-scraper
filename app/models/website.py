from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum
import app.models.user
import app.models.chat_session
import app.models.scrapedcontent
import app.models.apikey

class ScrapingStatus(enum.Enum):
    PENDING = "PENDING"
    SCRAPING = "SCRAPING"
    COMPLETED = "COMPLETED"

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

