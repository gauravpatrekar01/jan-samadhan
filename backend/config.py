import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.DATABASE_NAME = os.getenv("DATABASE_NAME", "jansamadhan")
        self.JWT_SECRET = os.getenv("JWT_SECRET", "")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        self.ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
        
        # AWS / S3 Configuration
        self.AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "")
        self.AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
        self.S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
        
        # Cloudinary Configuration
        self.CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
        self.CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
        self.CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

settings = Settings()
