from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.crud.base_crud import CRUDBase
from app.models.apikey import APIKey
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hashing_password


class CRUDUser(CRUDBase[User, UserCreate, BaseModel]):

    async def get_user_by_username(self, db: AsyncSession, username: str) -> User | None:
        """
        Asynchronously finds a user by their username.
        """

        statement = (
            select(User)
            .options(
                selectinload(User.api_keys).selectinload(APIKey.website)
            )
            .where(User.username == username)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """
        Creates a new user, hashing the password before saving.
        This overrides the base create method to include password hashing.
        """
        # Hash the password from the input schema
        hashed_pass = hashing_password(obj_in.password)

        # Create the SQLAlchemy model instance
        db_user = self.model(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=hashed_pass
        )

        # Add the new user to the session and commit the transaction
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return db_user


# Create a single instance to be used throughout your application
crud_user = CRUDUser(User)