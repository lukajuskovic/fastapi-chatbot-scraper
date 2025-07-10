import uuid
from requests.sessions import Session
from app.crud.base_crud import CRUDBase
from app.models.message import Message
from pydantic import BaseModel
from app.schemas.message import MessageCreate


class CRUDMessage(CRUDBase[Message,MessageCreate,BaseModel]):

    def get_messages_by_session(self, db: Session, session_id: uuid.UUID) -> list[Message]:
        return db.query(Message).filter(Message.chat_session_id == session_id).order_by(
            Message.time_created.desc()
        ).all()

crud_message = CRUDMessage(Message)