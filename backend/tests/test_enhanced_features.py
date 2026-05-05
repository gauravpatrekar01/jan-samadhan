#!/usr/bin/env python3
"""
Simple test to verify all enhanced features are working
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_features():
    print("🚀 JanSamadhan Enhanced Features Test")
    print("=" * 60)
    
    # Test 1: Environment Variables
    print("\n1️⃣ Testing Environment Variables:")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    
    print(f"   Cloudinary: {'✅ SET' if all([cloud_name, api_key, api_secret]) else '❌ MISSING'}")
    print(f"   MongoDB: {'✅ SET' if os.getenv('MONGODB_URI') else '❌ MISSING'}")
    
    # Test 2: Import New Modules
    print("\n2️⃣ Testing New Module Imports:")
    try:
        from services.media_service import upload_media, delete_media
        print("   ✅ Media Service: OK")
    except Exception as e:
        print(f"   ❌ Media Service: {e}")
    
    try:
        from services.prediction_service import get_complaint_predictions
        print("   ✅ Prediction Service: OK")
    except Exception as e:
        print(f"   ❌ Prediction Service: {e}")
    
    try:
        from routes.predictions import router as predictions_router
        print("   ✅ Predictions Router: OK")
    except Exception as e:
        print(f"   ❌ Predictions Router: {e}")
    
    try:
        from routes.public import router as public_router
        print("   ✅ Public Router: OK")
    except Exception as e:
        print(f"   ❌ Public Router: {e}")
    
    # Test 3: Cloudinary Configuration
    print("\n3️⃣ Testing Cloudinary:")
    try:
        import cloudinary
        import cloudinary.uploader
        print("   ✅ Cloudinary Import: OK")
        
        # Manual config test
        if all([cloud_name, api_key, api_secret]):
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret
            )
            print("   ✅ Cloudinary Config: OK")
        else:
            print("   ⚠️ Cloudinary Config: Missing env vars")
            
    except Exception as e:
        print(f"   ❌ Cloudinary: {e}")
    
    # Test 4: Database Connection
    print("\n4️⃣ Testing Database:")
    try:
        from db import db
        collection = db.get_collection("complaints")
        count = collection.count_documents({})
        print(f"   ✅ MongoDB Connection: OK ({count} complaints)")
    except Exception as e:
        print(f"   ❌ MongoDB: {e}")
    
    # Test 5: New API Endpoints
    print("\n5️⃣ Testing API Endpoints Structure:")
    try:
        from routes.complaints import router
        routes = [route.path for route in router.routes]
        new_routes = [
            "/with-media", "/vote", "/comment", "/comments", "/media/{public_id}"
        ]
        
        for route in new_routes:
            if any(route in r for r in routes):
                print(f"   ✅ {route}: Available")
            else:
                print(f"   ❌ {route}: Missing")
                
    except Exception as e:
        print(f"   ❌ API Routes: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced Features Test Complete!")
    
    # Summary
    print("\n📋 Ready to Use:")
    print("   • Media Upload: POST /api/complaints/with-media")
    print("   • Social Features: POST /api/complaints/{id}/vote")
    print("   • Predictions: GET /api/analytics/predictions")
    print("   • Public Dashboard: GET /api/public/stats")
    print("   • Start server: python app.py")

if __name__ == "__main__":
    asyncio.run(test_features())
