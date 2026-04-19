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
        try:
            cls.db["users"].create_index([("email", ASCENDING)], unique=True)
            cls.db["users"].create_index([("role", ASCENDING)])
            
            cls.db["complaints"].create_index([("id", ASCENDING)], unique=True)
            cls.db["complaints"].create_index([("grievanceID", ASCENDING)], unique=True)
            cls.db["complaints"].create_index([("citizen_email", ASCENDING)])
            cls.db["complaints"].create_index([("status", ASCENDING)])
            cls.db["complaints"].create_index([("priority", ASCENDING)])
            cls.db["complaints"].create_index([("region", ASCENDING)])
            cls.db["complaints"].create_index([("assigned_officer", ASCENDING)])
            cls.db["complaints"].create_index([("assigned_to_ngo", ASCENDING)])
            cls.db["complaints"].create_index([("sla_deadline", ASCENDING)])
            
            # Using location_geo for spatial to avoid conflicts with string 'location'
            cls.db["complaints"].create_index([("location_geo", "2dsphere")], sparse=True)
            
            cls.db["audit_logs"].create_index([("timestamp", ASCENDING)])
            cls.db["audit_logs"].create_index([("actor_email", ASCENDING)])
            cls.db["audit_logs"].create_index([("resource_id", ASCENDING)])

            cls.db["ngo_requests"].create_index([("ngo_email", ASCENDING)])
            cls.db["ngo_requests"].create_index([("complaint_id", ASCENDING)])
            cls.db["ngo_requests"].create_index([("status", ASCENDING)])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Database index creation encountered an issue: {e}")

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
