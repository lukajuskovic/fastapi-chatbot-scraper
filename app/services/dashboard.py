import multiprocessing
import uuid
from app.crud.crud_apikey import crud_api_key
from app.crud.crud_website import crud_website
from app.models.user import User
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.website import WebsiteCreate
from app.services.scraping import scrape_site
from app.api.deps import get_db


class DashboardService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def create_website_and_api_key(self, website_data: WebsiteCreate):
        existing_website = await crud_website.get_website_by_url(self.db, url=website_data.url)

        if existing_website is None:
            new_website = await crud_website.create(self.db, obj_in=website_data)

            scraper_process = multiprocessing.Process(
                target=scrape_site,
                args=(new_website.url, new_website.id)
            )
            scraper_process.start()
            web_id = new_website.id
        else:
            web_id = existing_website.id

        key_str = await crud_api_key.create(self.db, user_id=website_data.owner_id, website_id=web_id)
        if not key_str:
            raise HTTPException(status_code=500, detail="Could not generate a unique API key.")

        return key_str

    async def delete_api_key(self, key_id: uuid.UUID, current_user: User):
        key_to_delete = await crud_api_key.get_key_with_full_details(self.db, key_id=key_id)
        if not key_to_delete:
            raise HTTPException(status_code=404, detail="API key not found")
        if key_to_delete.user_id != current_user.id:
            raise HTTPException(status_code=401, detail="API key doesn't belong to current user")

        website = key_to_delete.website
        if len(website.api_keys) == 1:
            await crud_website.remove(self.db, id=website.id)
        else:
            await crud_api_key.remove(self.db, id=key_to_delete.id)