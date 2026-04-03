from pymongo import MongoClient
from config import settings

class Database:
    client: MongoClient = None
    db = None

    @classmethod
    def connect(cls):
        cls.client = MongoClient(settings.MONGO_URI)
        cls.db = cls.client[settings.DATABASE_NAME]

    @classmethod
    def get_collection(cls, name: str):
        if cls.db is None:
            cls.connect()
        return cls.db[name]

db = Database()
