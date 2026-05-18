import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app import app
from db import db
from security import create_access_token
import uuid

client = TestClient(app)

# 1. Setup Complaint
complaint_id = "TEST-APPROVAL-COMPLAINT-1"
db.get_collection("complaints").delete_one({"id": complaint_id})
db.get_collection("complaints").insert_one({
    "id": complaint_id,
    "grievanceID": "JSM-2026-TESTAPPROV",
    "title": "Water leakage in Ward 2",
    "description": "Water is leaking from main pipeline since two days.",
    "category": "Water Supply",
    "status": "submitted"
})

# 2. Setup NGO and Request
ngo_email = "contact@ngo.in"
db.get_collection("ngo_requests").delete_many({"ngo_email": ngo_email, "complaint_id": complaint_id})

# Set the NGO categories to standard ones
db.get_collection("users").update_one(
    {"email": ngo_email},
    {"$set": {"categories": ["Water Supply"], "verified": True, "is_active": True}}
)

# Submit Request
ngo_token = create_access_token({"sub": ngo_email, "role": "ngo"})
headers_ngo = {"Authorization": f"Bearer {ngo_token}"}
req_response = client.post("/api/ngo/requests", json={"complaint_id": complaint_id}, headers=headers_ngo)
print("Request POST Status:", req_response.status_code)
req_data = req_response.json()
print("Request POST Data:", req_data)

request_id = req_data["data"]["id"]

# 3. Approve Request as Admin
admin_email = "admin@example.com"
admin_token = create_access_token({"sub": admin_email, "role": "admin"})
headers_admin = {"Authorization": f"Bearer {admin_token}"}

approve_response = client.patch(f"/api/admin/ngo-requests/{request_id}/approve", headers=headers_admin)
print("\nApprove PATCH Status:", approve_response.status_code)
print("Approve PATCH Response:", approve_response.json())

# 4. Check Complaint in Database
complaint = db.get_collection("complaints").find_one({"id": complaint_id})
print("\nComplaint in DB after approval:")
print(f"assigned_to_ngo: {complaint.get('assigned_to_ngo')}")
print(f"status: {complaint.get('status')}")

# 5. Check Assigned Complaints for NGO
assigned_response = client.get("/api/ngo/assigned-complaints", headers=headers_ngo)
print("\nNGO Assigned Complaints Status:", assigned_response.status_code)
print("NGO Assigned Complaints Data:", assigned_response.json())
