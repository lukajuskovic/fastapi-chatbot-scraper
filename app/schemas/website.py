from pydantic import BaseModel
from app.models.chatbot import ScrapingStatus

class WebsiteCreate(BaseModel):
    url: str

class WebsiteInfo(BaseModel):
    id: int
    url: str
    scraping_status: ScrapingStatus