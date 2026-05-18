#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

import pytest
from fastapi.testclient import TestClient
from app import app
from db import db

client = TestClient(app)

def test_anonymous_complaint_lifecycle():
    # 1. Login as citizen to get token
    login_res = client.post("/api/auth/login", json={
        "email": "citizen@example.com",
        "password": "CitizenSecure123!"
    })
    assert login_res.status_code == 200, "Citizen login failed"
    token = login_res.json()["data"]["token"]
    citizen_headers = {"Authorization": f"Bearer {token}"}

    # 2. Login as admin to get token
    admin_login_res = client.post("/api/auth/admin-login", json={
        "email": "admin@example.com",
        "password": "AdminSecure123!"
    })
    assert admin_login_res.status_code == 200, "Admin login failed"
    admin_token = admin_login_res.json()["data"]["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Create anonymous complaint
    complaint_payload = {
        "title": "Water Leakage in Sector 4",
        "description": "Clean drinking water is leaking from the main pipeline since 2 days.",
        "category": "Water Supply",
        "subcategory": "Pipeline Leakage",
        "priority": "high",
        "location": "Sector 4, Near Water Tank",
        "region": "Nashik",
        "is_anonymous": True
    }
    
    create_res = client.post("/api/complaints/", json=complaint_payload, headers=citizen_headers)
    assert create_res.status_code == 201, f"Failed to create complaint: {create_res.text}"
    complaint_id = create_res.json()["data"]["id"]
    assert complaint_id is not None

    # Check database document directly
    collection = db.get_collection("complaints")
    doc = collection.find_one({"id": complaint_id})
    assert doc is not None
    assert doc.get("is_anonymous") is True
    assert doc.get("created_by_user_id") == "citizen@example.com"
    # Ensure the user link was NOT overwritten/lost
    assert doc.get("citizen_email") == "citizen@example.com"

    # 4. Get complaint details as citizen (non-admin) -> Should be masked
    get_citizen_res = client.get(f"/api/complaints/{complaint_id}", headers=citizen_headers)
    assert get_citizen_res.status_code == 200
    cit_data = get_citizen_res.json()["data"]
    assert cit_data.get("name") == "Anonymous"
    assert cit_data.get("citizen_email") == "Anonymous"
    assert cit_data.get("email") == "Anonymous"
    assert "created_by_user_id" not in cit_data

    # 5. Get complaint details as admin -> Should NOT be masked
    get_admin_res = client.get(f"/api/complaints/{complaint_id}", headers=admin_headers)
    assert get_admin_res.status_code == 200
    admin_data = get_admin_res.json()["data"]
    assert admin_data.get("name") != "Anonymous"
    assert admin_data.get("citizen_email") == "citizen@example.com"

    # 6. Verify internal audit log
    audit_coll = db.get_collection("audit_logs")
    audit_entry = audit_coll.find_one({"action": "anonymous_complaint_created", "resource_id": complaint_id})
    assert audit_entry is not None
    assert audit_entry.get("actor_email") == "citizen@example.com"
    assert audit_entry.get("details", {}).get("user_id") == "citizen@example.com"

    # Clean up test complaint and audit log
    collection.delete_one({"id": complaint_id})
    audit_coll.delete_one({"action": "anonymous_complaint_created", "resource_id": complaint_id})
    print("\n✅ Anonymous complaint backend lifecycle test PASSED successfully!")

if __name__ == "__main__":
    test_anonymous_complaint_lifecycle()
