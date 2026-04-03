from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "jansamadhan"
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
