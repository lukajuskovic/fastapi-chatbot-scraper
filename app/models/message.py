import uuid
from sqlalchemy import Column, ForeignKey, DateTime, Enum, func, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum
import app.models.chat_session

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

    # index for 'time_created' column in descending order.
    __table_args__ = (
        Index('messages_time_created_desc',chat_session_id, time_created.desc()),
    )