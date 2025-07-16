import secrets
import uuid
from typing import List
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_key
from app.crud.base_crud import CRUDBase
from app.models.apikey import APIKey
from app.models.website import Website
from app.schemas.api_key import APIKeyCreate


class CRUDAPIKey(CRUDBase[APIKey, APIKeyCreate, BaseModel]):

    async def find_by_prefix(self, db: AsyncSession, prefix: str) -> APIKey | None:
        """
        Asynchronously finds an API key by its prefix.
        """
        # Create a select statement
        statement = select(self.model).options(
                selectinload(self.model.user), # Eagerly load the User
                selectinload(self.model.website) # Eagerly load the Website
            ).where(self.model.prefix == prefix)
        # Execute the statement and get the single result
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, user_id: uuid.UUID, website_id: int) -> str:
        """
        Creates a new API key for a given user and website.
        This overrides the base create method to handle custom logic.
        Returns a dictionary with the unhashed key and the database object.
        """
        # Generate a new key and prefix
        new_key_str = f"{secrets.token_urlsafe(32)}"
        prefix = new_key_str[:8]

        # Check for prefix collision by calling our other method
        existing_key = await self.find_by_prefix(db, prefix=prefix)
        if existing_key:
            # We don't need to rollback here since we haven't committed anything yet
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Could not generate a unique API key, please try again.")

        # Create the SQLAlchemy model instance
        hashed_key_str = hash_key(new_key_str)
        db_api_key = APIKey(
            hashed_key=hashed_key_str,
            prefix=prefix,
            user_id=user_id,
            website_id=website_id
        )

        # Add the new object to the session and commit the transaction
        db.add(db_api_key)
        await db.commit()
        await db.refresh(db_api_key)

        return new_key_str

    async def get_multi_by_owner(
            self, db: AsyncSession, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[APIKey]:
        """
        Asynchronously gets a list of API keys belonging to a specific user.
        """
        # Create a select statement with a filter and pagination
        statement = (
            select(self.model)
            .where(self.model.user_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        # Execute the statement and get all results
        result = await db.execute(statement)
        return result.scalars().all()

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> APIKey | None:
        """
        Fetches an API key and eagerly loads the necessary relationships
        for the delete operation (the parent website and its other API keys).
        """
        statement = (
            select(self.model)
            .options(
                selectinload(self.model.website).selectinload(Website.api_keys)
            )
            .where(self.model.id == id)
        )
        result = await db.execute(statement)
        obj_to_delete = result.scalar_one_or_none()
        if obj_to_delete:
            await db.delete(obj_to_delete)
            await db.commit()
            return obj_to_delete
        return None

    async def get_key_with_full_details(self, db: AsyncSession, *, key_id: uuid.UUID) -> APIKey | None:
        """
        Fetches an API key and eagerly loads the website and the website's api_keys.
        This is the correct way to fetch data for the delete operation.
        """
        statement = (
            select(self.model)
            .options(
                selectinload(self.model.website).selectinload(Website.api_keys)
            )
            .where(self.model.id == key_id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

# Create a single instance to be used throughout your application
crud_api_key = CRUDAPIKey(APIKey)