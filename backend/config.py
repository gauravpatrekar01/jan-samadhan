from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "jansamadhan"
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: str = "*"

    # AWS / S3 Configuration
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
