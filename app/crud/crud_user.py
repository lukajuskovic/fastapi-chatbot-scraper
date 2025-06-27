# app/crud/crud_user.py
import uuid
from sqlalchemy.orm import Session
from app.models.user import User, APIKey
from app.schemas.user import UserCreate
from app.core.security import hashing_password, hash_key
import secrets


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: UserCreate) -> User:
    hashed_pass = hashing_password(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_pass)
    db.add(db_user)
    # The commit will be handled by the endpoint
    return db_user


def get_api_key(db: Session, key_id: uuid.UUID, user_id: uuid.UUID) -> APIKey | None:
    return db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()


def create_api_key_for_website(db: Session, user: User, website_id: int) -> tuple[str, APIKey]:
    new_key_str = f"{secrets.token_urlsafe(32)}"
    prefix = new_key_str[:8]

    # Check for prefix collision
    if db.query(APIKey).filter(APIKey.prefix == prefix).first():
        return None, None

    hashed_key_str = hash_key(new_key_str)
    db_api_key = APIKey(
        hashed_key=hashed_key_str,
        prefix=prefix,
        user_id=user.id,
        website_id=website_id
    )
    db.add(db_api_key)
    return new_key_str, db_api_key


def delete_api_key(db: Session, api_key: APIKey):
    db.delete(api_key)