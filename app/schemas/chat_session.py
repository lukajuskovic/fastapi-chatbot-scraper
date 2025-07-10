from pydantic import BaseModel

class ChatSessionCreate(BaseModel):
    website_id : int