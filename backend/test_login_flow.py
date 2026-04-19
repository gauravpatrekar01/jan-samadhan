#!/usr/bin/env python3
"""Test login flow for citizen and officer"""

import sys
sys.path.insert(0, '.')

from db import db
from security import verify_password
import json

def test_login_flow():
    """Test if credentials match and login should work"""
    collection = db.get_collection("users")
    
    test_credentials = [
        {"email": "citizen@example.com", "password": "CitizenSecure123!", "role": "citizen"},
        {"email": "officer@example.com", "password": "OfficerSecure123!", "role": "officer"},
        {"email": "admin@example.com", "password": "AdminSecure123!", "role": "admin"},
    ]
    
    print("\n🧪 Testing login credentials...\n")
    
    for cred in test_credentials:
        user = collection.find_one({"email": cred["email"]})
        if not user:
            print(f"❌ User {cred['email']} NOT FOUND in database")
            continue
        
        password_matches = verify_password(cred["password"], user["password"])
        role_matches = user.get("role") == cred["role"]
        
        status = "✅" if password_matches and role_matches else "❌"
        print(f"{status} {cred['email']} ({cred['role']})")
        print(f"   Password match: {password_matches}")
        print(f"   Role match: {role_matches}")
        print()

if __name__ == "__main__":
    test_login_flow()
