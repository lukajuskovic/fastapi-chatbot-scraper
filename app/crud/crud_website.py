from sqlalchemy.orm import Session

from app.crud.base_crud import CRUDBase
from app.models.website import Website, ScrapingStatus
from app.schemas.website import WebsiteCreate, WebsiteUpdate


class CRUDWebsite(CRUDBase[Website,WebsiteCreate,WebsiteUpdate]):

    def get_website_by_url(self, db: Session, url: str) -> Website | None:
        return db.query(Website).filter(Website.url == url).first()

crud_website = CRUDWebsite(Website)
