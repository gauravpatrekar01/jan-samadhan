#!/usr/bin/env python3
"""Create test users for notice management testing"""

import sys
sys.path.insert(0, '.')

from db import db
from security import hash_password
import uuid
from datetime import datetime, timezone

def create_test_users():
    """Create admin and officer test accounts"""
    collection = db.get_collection("users")
    
    users_to_create = [
        {
            "email": "admin@gov.in",
            "name": "System Admin",
            "password": hash_password("AdminSecure123!"),
            "role": "admin",
            "verified": True,
            "createdAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "email": "officer@gov.in",
            "name": "Field Officer",
            "password": hash_password("OfficerSecure123!"),
            "role": "officer",
            "verified": True,
            "department": "Public Works",
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for user in users_to_create:
        # Check if already exists
        if collection.find_one({"email": user["email"]}):
            print(f"✓ {user['email']} already exists")
        else:
            collection.insert_one(user)
            print(f"✅ Created {user['email']} ({user['role']})")

if __name__ == "__main__":
    print("🔐 Creating test users for notice management...\n")
    create_test_users()
    print("\n✅ Test users ready!")
