import sys
sys.path.insert(0, '.')
from db import db
from security import hash_password

users_coll = db.get_collection("users")
users_coll.update_one(
    {"email": "contact@ngo.in"},
    {"$set": {"password": hash_password("password123")}}
)
print("Reset NGO contact@ngo.in password to 'password123'")
