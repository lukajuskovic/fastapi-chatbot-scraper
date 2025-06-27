from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import find_dotenv

class Settings(BaseSettings):
    DB_NAME:str
    DB_USER:str
    DB_PASSWORD:str
    SECRET_KEY: str
    GOOGLE_API_KEY: str
    model_config = SettingsConfigDict(env_file=find_dotenv() , extra='ignore')

@lru_cache
def get_settings() -> Settings:
    return Settings()