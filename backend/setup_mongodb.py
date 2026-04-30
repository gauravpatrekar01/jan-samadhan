#!/usr/bin/env python3
"""
Setup MongoDB environment variable
"""
import os
from dotenv import load_dotenv, set_key

load_dotenv()

# Check if MongoDB URI is set
mongodb_uri = os.getenv("MONGODB_URI")

if not mongodb_uri:
    print("🔧 Setting up MongoDB URI...")
    
    # Default MongoDB URI for local development
    default_uri = "mongodb://localhost:27017/jansamadhan"
    
    try:
        # Update .env file
        env_file = ".env"
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Check if MONGODB_URI already exists
        has_mongodb = any(line.startswith("MONGODB_URI=") for line in lines)
        
        if not has_mongodb:
            with open(env_file, 'a') as f:
                f.write(f"\n# Database Configuration\nMONGODB_URI={default_uri}\n")
            print(f"✅ Added MongoDB URI to .env: {default_uri}")
        else:
            print("✅ MongoDB URI already exists in .env")
            
    except Exception as e:
        print(f"❌ Error setting up MongoDB: {e}")
else:
    print("✅ MongoDB URI already configured")

# Test the configuration
load_dotenv()  # Reload to get the new value
mongodb_uri = os.getenv("MONGODB_URI")
print(f"🔗 MongoDB URI: {mongodb_uri}")

# Test MongoDB connection
try:
    from pymongo import MongoClient
    client = MongoClient(mongodb_uri)
    client.admin.command('ping')
    print("✅ MongoDB connection: OK")
    client.close()
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

print("\n🚀 Ready to start the enhanced server!")
print("Run: python app.py")
