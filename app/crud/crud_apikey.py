import secrets
import uuid
from fastapi import HTTPException, Response, status
from typing import List
from sqlalchemy.orm import Session

from app.core.security import hash_key
from app.crud.base_crud import CRUDBase
from app.models.apikey import APIKey
from pydantic import BaseModel

from app.schemas.api_key import APIKeyCreate


class CRUDAPIKey(CRUDBase[APIKey, APIKeyCreate, BaseModel]):

    def create(self, db: Session, user_id: uuid.UUID, website_id: int) -> str:
        new_key_str = f"{secrets.token_urlsafe(32)}"
        prefix = new_key_str[:8]

        # Check for prefix collision
        if db.query(APIKey).filter(APIKey.prefix == prefix).first():
            db.rollback()
            raise HTTPException(status_code=500, detail="Could not generate a unique API key, please try again.")

        hashed_key_str = hash_key(new_key_str)
        db_api_key = APIKey(
            hashed_key=hashed_key_str,
            prefix=prefix,
            user_id=user_id,
            website_id=website_id
        )
        db.add(db_api_key)
        db.commit()
        return new_key_str

    def get_multi_by_owner(
            self, db: Session, *, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[APIKey]:
        """
        Get a list of API keys belonging to a specific user.
        """
        return (
            db.query(self.model)
            .filter(APIKey.user_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


crud_api_key = CRUDAPIKey(APIKey)