import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

print("1. Testing anonymous GET /api/complaints/")
res = client.get("/api/complaints/")
print("Status Code:", res.status_code)
try:
    print("JSON length:", len(res.json().get("data", [])))
except Exception as e:
    print("Error parsing JSON:", e, res.text)

print("\n2. Testing admin GET /api/complaints/")
# Let's login first as admin using the correct admin-login endpoint
login_res = client.post("/api/auth/admin-login", json={"email": "admin@example.com", "password": "AdminSecure123!"})
print("Login status:", login_res.status_code)
login_json = login_res.json()
print("Login success:", login_json.get("success"))
token = login_json.get("data", {}).get("token")
print("Token:", token)

res_admin = client.get("/api/complaints/", headers={"Authorization": f"Bearer {token}"})
print("Admin GET status:", res_admin.status_code)
try:
    data = res_admin.json().get("data", [])
    print("Admin JSON length:", len(data))
    # Check if any complaint doesn't have priority or status
    for i, c in enumerate(data):
        if "priority" not in c:
            print(f"Complaint {i} ({c.get('id')}) is missing priority!")
        if "status" not in c:
            print(f"Complaint {i} ({c.get('id')}) is missing status!")
except Exception as e:
    print("Error parsing Admin JSON:", e, res_admin.text)
