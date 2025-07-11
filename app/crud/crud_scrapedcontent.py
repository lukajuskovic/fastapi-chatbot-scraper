from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.crud.base_crud import CRUDBase
from app.models.scrapedcontent import ScrapedContent
from app.schemas.scrapedcontent import ScrapedContentCreate
from pgvector.sqlalchemy import Vector


class CRUDScrapedContent(CRUDBase[ScrapedContent, ScrapedContentCreate, BaseModel]):

    async def get_relevant_scraped_content(
        self, db: AsyncSession, website_id: int, embedding: List[float], top_k: int
    ) -> List[ScrapedContent]:
        """
        Finds the most relevant text chunks from the database
        using vector similarity search (L2 distance).
        """
        statement = (
            select(self.model)
            .filter(self.model.website_id == website_id)
            .order_by(self.model.embedding.l2_distance(embedding))
            .limit(top_k)
        )

        result = await db.execute(statement)

        return result.scalars().all()


crud_scraped_content = CRUDScrapedContent(ScrapedContent)