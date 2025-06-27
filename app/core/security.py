#To remove passlib bug
import bcrypt
bcrypt.__about__ = bcrypt
#####

import jwt
from passlib.context import CryptContext
from datetime import datetime,timedelta
from app.core.config import get_settings

settings = get_settings()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hashing_password(password: str):
    hashed_password = pwd_context.hash(password)
    return hashed_password


def verify_password(password: str,hashed_password: str):
    return pwd_context.verify(password, hashed_password)

def generate_jwt(username: str):
    expiration = datetime.now() + timedelta(minutes=30)
    payload = {
        "sub": username,
        "exp": expiration
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def hash_key(key: str) -> str:
    return api_key_context.hash(key)

def verify_key(key: str, hashed_key: str) -> bool:
    return api_key_context.verify(key, hashed_key)