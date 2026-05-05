#!/usr/bin/env python3
"""
Create Working Complaint Endpoint Test
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import os
from pymongo import MongoClient

# Simple FastAPI app for testing
app = FastAPI(title="Test Complaint API")

# Simple complaint model
class SimpleComplaint(BaseModel):
    title: str
    description: str
    category: str
    priority: str = "medium"
    location: str
    region: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# Database connection
def get_db():
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/jansamadhan")
    client = MongoClient(mongodb_uri)
    return client.get_database()

@app.post("/test-complaint")
async def create_test_complaint(complaint: SimpleComplaint):
    """Simple working complaint endpoint"""
    try:
        db = get_db()
        
        # Create complaint document
        complaint_doc = {
            "title": complaint.title,
            "description": complaint.description,
            "category": complaint.category,
            "priority": complaint.priority,
            "location": complaint.location,
            "region": complaint.region,
            "latitude": complaint.latitude,
            "longitude": complaint.longitude,
            "status": "submitted",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "grievanceID": f"JSM-{datetime.now().year}-TEST{datetime.now().second}",
            "id": f"JSM-{datetime.now().year}-TEST{datetime.now().second}",
            "votes": 0,
            "comments": [],
            "media": [],
            "timeline": [
                {
                    "stage": "Submitted",
                    "remarks": "Test complaint submitted",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "updated_by_user_id": "test@example.com"
                }
            ]
        }
        
        # Insert into database
        result = db.complaints.insert_one(complaint_doc)
        
        if result.inserted_id:
            return {
                "success": True,
                "data": {
                    "id": complaint_doc["id"],
                    "grievanceID": complaint_doc["grievanceID"],
                    "status": "submitted",
                    "message": "Test complaint created successfully"
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert complaint")
            
    except Exception as e:
        print(f"Error in test endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/test-status")
def get_test_status():
    """Check if test API is working"""
    return {
        "success": True,
        "message": "Test complaint API is running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Test Complaint API on http://localhost:8001")
    print("📋 Test this endpoint:")
    print("   curl -X POST http://localhost:8001/test-complaint \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"title\":\"Test\",\"description\":\"Test complaint\",\"category\":\"Infrastructure\",\"location\":\"Test\",\"region\":\"Test\"}'")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
