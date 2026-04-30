#!/usr/bin/env python3
"""
Session Status Checker
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

load_dotenv()

print("🔍 JanSamadhan Session Status Check")
print("=" * 50)

# Check environment variables
print("\n📋 Environment Variables:")
print(f"   MongoDB: {'✅ SET' if os.getenv('MONGODB_URI') else '❌ MISSING'}")
print(f"   JWT Secret: {'✅ SET' if os.getenv('JWT_SECRET') else '❌ MISSING'}")

# Check database connection
print("\n🗄️ Database Status:")
try:
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/jansamadhan")
    client = MongoClient(mongodb_uri)
    db = client.get_database()
    
    # Check collections
    collections = db.list_collection_names()
    print(f"   Connected: ✅")
    print(f"   Collections: {len(collections)}")
    
    # Check users
    if "users" in collections:
        users_count = db.users.count_documents({})
        print(f"   Users: {users_count}")
    
    # Check complaints
    if "complaints" in collections:
        complaints_count = db.complaints.count_documents({})
        print(f"   Complaints: {complaints_count}")
        
        # Check recent complaints
        recent = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_count = db.complaints.count_documents({
            "createdAt": {"$gte": recent.isoformat()}
        })
        print(f"   Last 24h: {recent_count}")
    
    client.close()
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check server status
print("\n🌐 Server Status:")
try:
    import requests
    response = requests.get("http://localhost:8000/", timeout=5)
    if response.status_code == 200:
        print("   API Server: ✅ Running")
    else:
        print(f"   API Server: ⚠️ Status {response.status_code}")
except Exception as e:
    print(f"   API Server: ❌ Not reachable ({e})")

# Check Cloudinary
print("\n☁️ Cloudinary Status:")
cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

if all([cloud_name, api_key, api_secret]):
    print("   Configuration: ✅ SET")
    try:
        import cloudinary
        print("   Library: ✅ Available")
        print("   Ready: ✅ Media uploads enabled")
    except Exception as e:
        print(f"   Library: ❌ Error: {e}")
else:
    print("   Configuration: ❌ MISSING")

print("\n" + "=" * 50)
print("🔧 Troubleshooting Tips:")
print("   1. If session expired, simply login again at index.html")
print("   2. Check browser console for automatic token refresh attempts")
print("   3. Ensure localStorage/sessionStorage has refresh_token")
print("   4. Server should auto-refresh tokens if refresh_token exists")
print("   5. If issues persist, clear browser cache and login again")

print("\n🚀 Quick Actions:")
print("   • Test login: Open index.html")
print("   • Check API: curl http://localhost:8000/")
print("   • View complaints: Login and check dashboard")
print("   • Test media: Try creating complaint with files")

print("\n" + "=" * 50)
