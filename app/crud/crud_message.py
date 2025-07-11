import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.crud.base_crud import CRUDBase
from app.models.message import Message
from app.schemas.message import MessageCreate


class CRUDMessage(CRUDBase[Message, MessageCreate, BaseModel]):

    async def get_messages_by_session(self, db: AsyncSession, session_id: uuid.UUID) -> List[Message]:
        statement = (
            select(self.model)
            .where(self.model.chat_session_id == session_id)
            .order_by(self.model.time_created.desc())
        )

        result = await db.execute(statement)

        return result.scalars().all()


crud_message = CRUDMessage(Message)