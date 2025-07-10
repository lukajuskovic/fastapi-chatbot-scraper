import uuid
from pydantic import BaseModel
from app.models.website import ScrapingStatus

class WebsiteCreate(BaseModel):
    url: str
    owner_id: uuid.UUID

class WebsiteInfo(BaseModel):
    id: int
    url: str
    scraping_status: ScrapingStatus

class WebsiteURLRequest(BaseModel):
    url: str

class WebsiteUpdate(BaseModel):
    scraping_status: ScrapingStatus