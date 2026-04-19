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
        cls.db["users"].create_index([("role", ASCENDING)])
        
        cls.db["complaints"].create_index([("id", ASCENDING)], unique=True)
        cls.db["complaints"].create_index([("grievanceID", ASCENDING)], unique=True)
        cls.db["complaints"].create_index([("citizen_email", ASCENDING)])
        cls.db["complaints"].create_index([("status", ASCENDING)])
        cls.db["complaints"].create_index([("priority", ASCENDING)])
        cls.db["complaints"].create_index([("region", ASCENDING)])
        cls.db["complaints"].create_index([("assigned_officer", ASCENDING)])
        cls.db["complaints"].create_index([("assigned_ngo", ASCENDING)])
        cls.db["complaints"].create_index([("sla_deadline", ASCENDING)])
        cls.db["complaints"].create_index([("location", "2dsphere")])
        
        cls.db["audit_logs"].create_index([("timestamp", ASCENDING)])
        cls.db["audit_logs"].create_index([("actor_email", ASCENDING)])
        cls.db["audit_logs"].create_index([("resource_id", ASCENDING)])

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
