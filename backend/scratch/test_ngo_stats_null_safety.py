import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app import app
from db import db

client = TestClient(app)

# 1. Login to get token for contact@ngo.in
login_res = client.post("/api/auth/login", json={"email": "contact@ngo.in", "password": "password123"})
assert login_res.status_code == 200, f"Login failed: {login_res.text}"
token = login_res.json()["data"]["token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Insert a complaint with feedback containing a None rating to explicitly simulate the bug condition
complaints_coll = db.get_collection("complaints")
complaints_coll.insert_one({
    "id": "JSM-2026-TEST-STATS-CRASH",
    "grievanceID": "JSM-2026-TEST-STATS-CRASH",
    "assigned_to_ngo": "contact@ngo.in",
    "status": "resolved",
    "feedback": {
        "remarks": "Great work!",
        "rating": None  # Null rating to trigger potential NoneType aggregate
    }
})

try:
    print("Testing GET /api/ngo/stats...")
    res = client.get("/api/ngo/stats", headers=headers)
    print("Status Code:", res.status_code)
    print("Response JSON:", res.json())
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "avg_rating" in res.json()["data"]
    print("✅ NGO stats test passed flawlessly!")
finally:
    # Cleanup
    complaints_coll.delete_one({"id": "JSM-2026-TEST-STATS-CRASH"})
