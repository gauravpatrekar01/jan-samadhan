import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app import app
from db import db
from security import create_access_token

client = TestClient(app)

# 1. Create a dummy complaint to use in this test
complaint_id = "TEST-JSM-COMPLAINT-1234"
db.get_collection("complaints").delete_one({"id": complaint_id})
db.get_collection("complaints").insert_one({
    "id": complaint_id,
    "title": "Broken Sanitation Toilets in Ward 5",
    "description": "The public toilets in Ward 5 are completely broken and unusable.",
    "category": "Sanitation",
    "status": "submitted"
})

# 2. Get the NGO contact@ngo.in token
ngo_email = "contact@ngo.in"
token = create_access_token({"sub": ngo_email, "role": "ngo"})

headers = {
    "Authorization": f"Bearer {token}"
}

# Cleanup existing requests for clean runs
db.get_collection("ngo_requests").delete_many({"ngo_email": ngo_email, "complaint_id": complaint_id})

print("1. Testing valid request payload:")
response = client.post("/api/ngo/requests", json={"complaint_id": complaint_id}, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.json())
print("-" * 50)

print("2. Testing invalid Content-Type:")
bad_headers = headers.copy()
bad_headers["Content-Type"] = "text/plain"
response = client.post("/api/ngo/requests", data="complaint_id=" + complaint_id, headers=bad_headers)
print("Status Code:", response.status_code)
print("Response:", response.json())
print("-" * 50)

print("3. Testing invalid JSON structure:")
response = client.post("/api/ngo/requests", content="{badjson: ", headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.json())
print("-" * 50)

print("4. Testing missing required fields (validation failure):")
response = client.post("/api/ngo/requests", json={"admin_remarks": "Test remarks"}, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.json())
print("-" * 50)
