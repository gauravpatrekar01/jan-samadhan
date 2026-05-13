from db import db

def debug_users():
    collection = db.get_collection("users")
    users = list(collection.find({"role": {"$in": ["ngo", "NGO"]}}).limit(5))
    
    for u in users:
        print(f"User: {u.get('email')}")
        print(f"  role: '{u.get('role')}' (type: {type(u.get('role'))})")
        print("-" * 30)

if __name__ == "__main__":
    debug_users()
