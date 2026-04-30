#!/usr/bin/env python3
"""
Create Simple Working Complaint Endpoint
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import os
from pymongo import MongoClient

# Simple FastAPI app for bypass
app = FastAPI(title="Bypass Complaint API")

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

@app.post("/bypass-complaint")
async def create_bypass_complaint(complaint: SimpleComplaint):
    """Bypass complaint endpoint to isolate issue"""
    try:
        db = get_db()
        
        # Create complaint document with minimal fields
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
            "grievanceID": f"JSM-{datetime.now().year}-BYPASS{datetime.now().second()}",
            "id": f"JSM-{datetime.now().year}-BYPASS{datetime.now().second()}",
            "votes": 0,
            "comments": [],
            "media": [],
            "timeline": [
                {
                    "stage": "Submitted",
                    "remarks": "Bypass complaint submitted",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "updated_by_user_id": "bypass_user"
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
                    "message": "Bypass complaint created successfully",
                    "createdAt": complaint_doc["createdAt"]
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert bypass complaint")
            
    except Exception as e:
        print(f"Error in bypass endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Bypass error: {str(e)}")

@app.get("/bypass-status")
def get_bypass_status():
    """Check if bypass API is working"""
    return {
        "success": True,
        "message": "Bypass complaint API is running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "usage": "POST /bypass-complaint with SimpleComplaint model"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting BYPASS Complaint API on http://localhost:8002")
    print("📋 Use this to test complaint creation if main endpoint fails:")
    print("   curl -X POST http://localhost:8002/bypass-complaint \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"title\":\"Test\",\"description\":\"Test complaint\",\"category\":\"Infrastructure\",\"location\":\"Test\",\"region\":\"Test\"}'")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)
