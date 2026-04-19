from pymongo import MongoClient, ASCENDING
from config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]

print("Attempting to create indexes manually to find the culprit...")
collections = ["users", "complaints", "audit_logs"]

for coll_name in collections:
    coll = db[coll_name]
    print(f"\nChecking collection: {coll_name}")
    
    if coll_name == "users":
        try: coll.create_index([("email", ASCENDING)], unique=True); print("Success: users.email (unique)")
        except Exception as e: print(f"FAIL: users.email -> {e}")
        try: coll.create_index([("role", ASCENDING)]); print("Success: users.role")
        except Exception as e: print(f"FAIL: users.role -> {e}")
        
    elif coll_name == "complaints":
        indexes = [
            ([("id", ASCENDING)], {"unique": True}),
            ([("grievanceID", ASCENDING)], {"unique": True}),
            ([("citizen_email", ASCENDING)], {}),
            ([("status", ASCENDING)], {}),
            ([("priority", ASCENDING)], {}),
            ([("region", ASCENDING)], {}),
            ([("location", "2dsphere")], {}),
        ]
        for keys, opts in indexes:
            try:
                coll.create_index(keys, **opts)
                print(f"Success: {keys}")
            except Exception as e:
                print(f"FAIL: {keys} -> {e}")
