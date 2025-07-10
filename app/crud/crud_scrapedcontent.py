from sqlalchemy.orm import Session
from app.crud.base_crud import CRUDBase
from pydantic import BaseModel
from app.models.scrapedcontent import ScrapedContent
from app.schemas.scrapedcontent import ScrapedContentCreate


class CRUDScrapedContent(CRUDBase[ScrapedContent, ScrapedContentCreate, BaseModel]):

    def get_relevant_scraped_content(self, db: Session, website_id: int, embedding: list[float], top_k: int) -> list[
        ScrapedContent]:
        return db.query(ScrapedContent).filter(
            ScrapedContent.website_id == website_id
        ).order_by(
            ScrapedContent.embedding.l2_distance(embedding)
        ).limit(top_k).all()


crud_scraped_content = CRUDScrapedContent(ScrapedContent)