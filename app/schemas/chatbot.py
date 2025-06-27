from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    session_id: str | None = None  # Optional for stateless vs. stateful chats


class ChatResponse(BaseModel):
    answer: str
    session_id: str