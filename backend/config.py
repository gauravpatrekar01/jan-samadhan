import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.DATABASE_NAME = os.getenv("DATABASE_NAME", "jansamadhan")
        self.JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY", "fallback-secret-key")
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
        
        # Gemini AI Configuration
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.GEMINI_API_KEY2 = os.getenv("GEMINI_API_KEY2", "")

        # SMS Gateway Configuration
        self.SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "http://192.168.1.5:3000/send")
        self.SMS_GATEWAY_TOKEN = os.getenv("SMS_GATEWAY_TOKEN", "")
        self.DEVICE_ID = os.getenv("DEVICE_ID", "")
        
        self.OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
        self.ESCALATION_DAYS = int(os.getenv("ESCALATION_DAYS", "7"))
        self.MAX_SMS_RETRIES = int(os.getenv("MAX_SMS_RETRIES", "3"))
        self.SMS_TIMEOUT_SECONDS = int(os.getenv("SMS_TIMEOUT_SECONDS", "10"))
        self.DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
        self.SENDER_NAME = os.getenv("SENDER_NAME", "JANSYS")
        self.SMS_DEBUG = os.getenv("SMS_DEBUG", "false").lower() == "true"

settings = Settings()
