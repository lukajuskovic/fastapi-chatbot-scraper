from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from .website import WebsiteInfo

class APIKeyInfo(BaseModel):
    id: uuid.UUID
    prefix: str
    website: WebsiteInfo
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class APIKeyResponse(BaseModel):
    key: str
    message: str