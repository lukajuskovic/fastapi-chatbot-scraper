from sqlalchemy import Column, Integer, String, ForeignKey, Text
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from app.db.base import Base
import app.models.website


class ScrapedContent(Base):
    __tablename__ = "scraped_content"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False, index=True)
    text_content = Column(Text, nullable=False)
    source_url = Column(String(2048))
    image_url = Column(String(2048), nullable=True)
    embedding = Column(Vector(384), nullable=True)

    website = relationship("Website", back_populates="scraped_content")