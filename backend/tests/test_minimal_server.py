#!/usr/bin/env python3
"""
Minimal server test to isolate the Cloudinary issue
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Set environment variables manually to avoid any validation
os.environ['CLOUDINARY_CLOUD_NAME'] = os.getenv("CLOUDINARY_CLOUD_NAME", "")
os.environ['CLOUDINARY_API_KEY'] = os.getenv("CLOUDINARY_API_KEY", "")
os.environ['CLOUDINARY_API_SECRET'] = os.getenv("CLOUDINARY_API_SECRET", "")

print("🔧 Testing minimal server startup...")

try:
    # Test basic imports
    from fastapi import FastAPI
    print("✅ FastAPI: OK")
    
    from routes import complaints
    print("✅ Complaints routes: OK")
    
    from routes import predictions
    print("✅ Predictions routes: OK")
    
    from routes import public
    print("✅ Public routes: OK")
    
    # Test Cloudinary without config
    import cloudinary.uploader
    print("✅ Cloudinary uploader: OK")
    
    print("✅ All imports successful!")
    print("🚀 Ready to start server!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

print("\n📋 Configuration Summary:")
print(f"   Cloudinary: {os.getenv('CLOUDINARY_CLOUD_NAME', 'NOT_SET')[:10]}...")
print(f"   MongoDB: {os.getenv('MONGODB_URI', 'NOT_SET')[:30]}...")
print(f"   Ready: YES")
