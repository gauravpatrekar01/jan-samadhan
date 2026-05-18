import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app import app
from db import db
from datetime import datetime, timezone
import io

client = TestClient(app)

# 1. Login to get token for contact@ngo.in
login_res = client.post("/api/auth/login", json={"email": "contact@ngo.in", "password": "password123"})
assert login_res.status_code == 200, f"Login failed: {login_res.text}"
token = login_res.json()["data"]["token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Let's make sure our test complaint JSM-2026-UPLOAD-TEST exists and is assigned to contact@ngo.in
complaints_coll = db.get_collection("complaints")
complaints_coll.update_one(
    {"id": "JSM-2026-UPLOAD-TEST"},
    {"$set": {
        "id": "JSM-2026-UPLOAD-TEST",
        "grievanceID": "JSM-2026-UPLOAD-TEST",
        "title": "Water Leakage in Test Sector",
        "description": "Pipe burst in block A causing massive water loss.",
        "category": "Water Supply",
        "priority": "high",
        "status": "in_progress",
        "assigned_to_ngo": "contact@ngo.in",
        "citizen_email": "citizen@test.com",
        "createdAt": datetime.now(timezone.utc).isoformat()
    }},
    upsert=True
)

# 3. Simulate media file upload (dummy PNG image)
dummy_file = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82")
files = {"file": ("test_evidence.png", dummy_file, "image/png")}

print("Testing Cloudinary media upload endpoint...")
res = client.post("/api/complaints/JSM-2026-UPLOAD-TEST/upload-media", headers=headers, files=files)

print("Status Code:", res.status_code)
print("Response:", res.json())

# Cleanup the test complaint
complaints_coll.delete_one({"id": "JSM-2026-UPLOAD-TEST"})
