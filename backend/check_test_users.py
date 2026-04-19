#!/usr/bin/env python3
"""Check existing users and create comprehensive test users"""

import sys
sys.path.insert(0, '.')

from db import db
from security import hash_password
from datetime import datetime, timezone

def check_and_create_users():
    """Check existing users and create test accounts if needed"""
    collection = db.get_collection("users")
    
    test_users = [
        {
            "email": "citizen@example.com",
            "name": "Test Citizen",
            "password": hash_password("CitizenSecure123!"),
            "role": "citizen",
            "aadhar": "123456789012",
            "verified": True,
            "createdAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "email": "officer@example.com",
            "name": "Test Officer",
            "password": hash_password("OfficerSecure123!"),
            "role": "officer",
            "verified": True,
            "department": "Public Works",
            "createdAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "email": "admin@example.com",
            "name": "Test Admin",
            "password": hash_password("AdminSecure123!"),
            "role": "admin",
            "verified": True,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    print("\n📊 Checking existing users...\n")
    for user in test_users:
        existing = collection.find_one({"email": user["email"]})
        if existing:
            print(f"✓ {user['email']} ({user['role']}) - EXISTS")
        else:
            collection.insert_one(user)
            print(f"✅ {user['email']} ({user['role']}) - CREATED")
    
    print("\n📋 All available users:")
    all_users = collection.find({})
    for user in all_users:
        print(f"  • {user.get('email')} ({user.get('role')})")

if __name__ == "__main__":
    print("🔐 Checking and creating test users...\n")
    check_and_create_users()
    print("\n✅ Test users ready!")
