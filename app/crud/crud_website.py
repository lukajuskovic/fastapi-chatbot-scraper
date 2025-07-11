from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base_crud import CRUDBase
from app.models.website import Website, ScrapingStatus
from app.schemas.website import WebsiteCreate, WebsiteUpdate


class CRUDWebsite(CRUDBase[Website,WebsiteCreate,WebsiteUpdate]):

    async def get_website_by_url(self, db: AsyncSession, url: str) -> Website | None:
        statement = select(self.model).where(self.model.url == url)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

crud_website = CRUDWebsite(Website)
