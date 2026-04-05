from pymongo import MongoClient, ASCENDING
from config import settings


class Database:
    client: MongoClient = None
    db = None

    @classmethod
    def connect(cls):
        cls.client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        cls.db = cls.client[settings.DATABASE_NAME]
        cls._ensure_indexes()

    @classmethod
    def _ensure_indexes(cls):
        cls.db["users"].create_index([("email", ASCENDING)], unique=True)
        cls.db["complaints"].create_index([("id", ASCENDING)], unique=True)
        cls.db["complaints"].create_index([("email", ASCENDING)])
        cls.db["complaints"].create_index([("status", ASCENDING)])

    @classmethod
    def disconnect(cls):
        if cls.client:
            cls.client.close()

    @classmethod
    def get_collection(cls, name: str):
        if cls.db is None:
            cls.connect()
        return cls.db[name]


db = Database()
