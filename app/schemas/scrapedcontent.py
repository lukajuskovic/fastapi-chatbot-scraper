from pydantic import BaseModel
from typing import Optional, List

class ScrapedContentCreate(BaseModel):
    website_id: int
    text_content: str
    source_url: str
    image_url: Optional[str] = None
    embedding: Optional[List[float]] = None