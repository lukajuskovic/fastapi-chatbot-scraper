from app.crud.base_crud import CRUDBase
from app.models.chat_session import Chat_session
from pydantic import BaseModel
from app.schemas.chat_session import ChatSessionCreate


class CRUDChatSession(CRUDBase[Chat_session,ChatSessionCreate,BaseModel]):
    pass

crud_chat_session = CRUDChatSession(Chat_session)