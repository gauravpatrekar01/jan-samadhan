#!/usr/bin/env python3
"""
Test Complaint Creation Directly
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

load_dotenv()

def test_database_direct():
    print("🔍 TESTING DATABASE COMPLAINT CREATION")
    print("=" * 50)
    
    try:
        # Connect to database
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/jansamadhan")
        client = MongoClient(mongodb_uri)
        db = client.get_database()
        
        print("✅ Database connected")
        
        # Check collections
        collections = db.list_collection_names()
        print(f"   Collections: {collections}")
        
        # Create a test complaint directly in database
        test_complaint = {
            "title": "Direct Database Test Complaint",
            "description": "This complaint is being inserted directly into the database to test if the issue is with the database schema or the API logic.",
            "category": "Infrastructure",
            "subcategory": "",
            "priority": "medium",
            "location": "Test Location",
            "region": "Test Region",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "citizen_email": "test@example.com",
            "status": "submitted",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "grievanceID": f"JSM-{datetime.now().year}-TEST123",
            "id": f"JSM-{datetime.now().year}-TEST123",
            "votes": 0,
            "comments": [],
            "media": [],
            "marathi_summary": None,
            "summary_generated": False,
            "timeline": [
                {
                    "stage": "Submitted",
                    "remarks": "Grievance filed by citizen",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "updated_by_user_id": "test@example.com"
                }
            ],
            "feedback": [],
            "feedbackAverage": 0,
            "feedbackCount": 0,
            "assigned_officer": None,
            "assigned_to_ngo": None,
            "sla_deadline": (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat()
        }
        
        print("\n📝 Inserting test complaint directly into database...")
        
        # Insert into complaints collection
        result = db.complaints.insert_one(test_complaint)
        
        if result.inserted_id:
            print("✅ Direct database insertion: SUCCESS!")
            print(f"   Inserted ID: {result.inserted_id}")
            
            # Query it back to verify
            retrieved = db.complaints.find_one({"id": test_complaint["id"]})
            if retrieved:
                print("✅ Verification: Can retrieve complaint")
                print(f"   Title: {retrieved['title']}")
                print(f"   Status: {retrieved['status']}")
            else:
                print("❌ Verification: Cannot retrieve complaint")
                
        else:
            print("❌ Direct database insertion: FAILED!")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSTIC RESULT:")
    print("If direct database works → Issue is in API layer")
    print("If direct database fails → Issue is in database/schema")
    print("\n📋 NEXT STEPS:")
    print("1. Check if your existing users have valid Aadhar numbers")
    print("2. Try the test user credentials provided above")
    print("3. Use browser DevTools to monitor network requests")
    print("4. Check server console for detailed error logs")

if __name__ == "__main__":
    test_database_direct()
