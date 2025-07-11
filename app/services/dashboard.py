import multiprocessing
import uuid

from app.crud.crud_apikey import crud_api_key
from app.crud.crud_website import crud_website
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.website import WebsiteCreate
from app.services.scraping import scrape_site


async def make_apikey(website_data: WebsiteCreate,
        db: AsyncSession):
    """
        Creates a new Website record and an associated API key.
        Starts the scraping process in a separate background process.
        """
    # Check if the website already exists. If not, create it.
    existing_website = await crud_website.get_website_by_url(db, website_data.url)
    if existing_website is None:
        new_website = await crud_website.create(db,obj_in = website_data)

        # Start the scraping function in a completely separate process
        # This prevents it from blocking the web server.
        scraper_process = multiprocessing.Process(
            target=scrape_site,
            args=(new_website.url, new_website.id)
        )
        scraper_process.start()

        web_id = new_website.id
    else:
        web_id = existing_website.id

    res = await crud_api_key.create(db,website_data.owner_id,web_id)
    return res


async def removing_apikey(key_id: uuid.UUID, db: AsyncSession, current_user: User):

    key_to_delete = await crud_api_key.get_key_with_full_details(db, key_id=key_id)

    if not key_to_delete or key_to_delete.user_id!=current_user.id:
        raise HTTPException(status_code=404, detail="API key not found")
    if key_to_delete.user_id!=current_user.id:
        raise HTTPException(status_code=401, detail="API key doesn't belong to current user")

    website = key_to_delete.website
    if len(website.api_keys) == 1:
        await crud_website.remove(db, id = website.id)
    else:
        await crud_api_key.remove(db, id = key_to_delete.id)