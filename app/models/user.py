import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import app.models.apikey
import app.models.website


class User(Base):
    __tablename__="users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email=Column(String,unique=True,index=True,nullable=False)
    username=Column(String,unique=True,index=True,nullable=False)
    hashed_password=Column(String,nullable=False)

    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    websites = relationship( "Website", back_populates="owner", cascade="all, delete-orphan")

