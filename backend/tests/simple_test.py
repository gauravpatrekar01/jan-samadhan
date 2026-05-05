#!/usr/bin/env python3
"""
Simple Cloudinary Test
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Simple Cloudinary Test:")
print("=" * 40)

cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY") 
api_secret = os.getenv("CLOUDINARY_API_SECRET")

print(f"Cloud Name: {cloud_name[:10]}..." if cloud_name else \"❌ NOT SET\"}")
print(f"API Key: {'✅ SET' if api_key else '❌ NOT SET'}")
print(f"API Secret: {'✅ SET' if api_secret else '❌ NOT SET'}")

if all([cloud_name, api_key, api_secret]):
    print("\n✅ Cloudinary environment variables are configured!")
    
    try:
        import cloudinary.uploader
        print("✅ Cloudinary uploader import: OK")
        
        # Manual config
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        print("✅ Cloudinary manual config: OK")
        print("✅ Ready for media uploads!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("\n❌ Missing Cloudinary environment variables")

print("\n" + "=" * 40)
