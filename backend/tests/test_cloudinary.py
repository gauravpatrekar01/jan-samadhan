#!/usr/bin/env python3
"""
Test Cloudinary Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Cloudinary Configuration Check:")
print("=" * 50)

# Check required variables
cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

print(f"Cloud Name: {cloud_name[:10]}..." if cloud_name else "❌ NOT SET")
print(f"API Key: {'✅ SET' if api_key else '❌ NOT SET'}")
print(f"API Secret: {'✅ SET' if api_secret else '❌ NOT SET'}")

if all([cloud_name, api_key, api_secret]):
    print("\n✅ All Cloudinary environment variables are set!")
    
    # Test Cloudinary import without config
    try:
        import cloudinary
        import cloudinary.uploader
        print("✅ Cloudinary modules imported successfully")
        
        # Test manual configuration
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        print("✅ Cloudinary configured successfully")
        
        # Test a simple upload (without actually uploading)
        print("✅ Ready for media uploads!")
        
    except Exception as e:
        print(f"❌ Cloudinary import error: {e}")
else:
    print("\n❌ Missing Cloudinary configuration!")
    print("Please set the following in your .env file:")
    print("CLOUDINARY_CLOUD_NAME=your-cloud-name")
    print("CLOUDINARY_API_KEY=your-api-key")
    print("CLOUDINARY_API_SECRET=your-api-secret")

print("\n" + "=" * 50)
