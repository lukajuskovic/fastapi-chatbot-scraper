import uuid
from pydantic import BaseModel
from app.models.message import MessageSender


class MessageCreate(BaseModel):
    chat_session_id: uuid.UUID
    sender: MessageSender
    text: str