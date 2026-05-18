import sys
sys.path.insert(0, '.')
from db import db

users_coll = db.get_collection("users")
ngo = users_coll.find_one({"email": "contact@ngo.in"})
if ngo:
    print("Found contact@ngo.in. Current categories:", ngo.get("categories"))
    # Normalize categories to standard ones
    users_coll.update_one(
        {"email": "contact@ngo.in"},
        {"$set": {"categories": ["Healthcare", "Sanitation", "Environment", "Health"]}}
    )
    print("Updated categories successfully!")
else:
    print("NGO not found!")
