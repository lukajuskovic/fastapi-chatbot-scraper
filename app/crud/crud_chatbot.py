# app/crud/crud_chatbot.py
import uuid
from sqlalchemy.orm import Session
from app.models.chatbot import Chat_session, Message, MessageSender

def get_session(db: Session, session_id: uuid.UUID) -> Chat_session | None:
    return db.query(Chat_session).filter(Chat_session.id == session_id).first()

def create_session(db: Session, website_id: int) -> Chat_session:
    db_session = Chat_session(id=uuid.uuid4(), website_id=website_id)
    db.add(db_session)
    return db_session

def get_messages_by_session(db: Session, session_id: uuid.UUID) -> list[Message]:
    return db.query(Message).filter(Message.chat_session_id == session_id).order_by(
        Message.time_created.desc()
    ).all()

def create_message(db: Session, session_id: uuid.UUID, sender: MessageSender, text: str) -> Message:
    db_message = Message(chat_session_id=session_id, sender=sender, text=text)
    db.add(db_message)
    return db_message