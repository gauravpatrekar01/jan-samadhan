import pytest
from fastapi.testclient import TestClient
import sys
import os
import datetime

# Add the backend directory to sys.path to import modules easily
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.dirname(__file__))

from limiter import limiter
limiter.enabled = False

from app import app
from db import db

client = TestClient(app)

CITIZEN_EMAIL = "citizen@example.com"
CITIZEN_PASS = "CitizenSecure123!"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASS = "AdminSecure123!"

_TOKEN_CACHE = {}

def get_token(email, password):
    if email in _TOKEN_CACHE:
        return _TOKEN_CACHE[email]
        
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        # Try admin login if standard login fails
        response = client.post("/api/auth/admin-login", json={"email": email, "password": password})
        
    token = response.json()["data"]["token"]
    _TOKEN_CACHE[email] = token
    return token

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Setup database with users and clean up complaints before tests."""
    db.get_collection("complaints").delete_many({"title": {"$regex": "^TEST_LIFECYCLE"}})
    yield
    # Teardown
    db.get_collection("complaints").delete_many({"title": {"$regex": "^TEST_LIFECYCLE"}})
    db.get_collection("audit_logs").delete_many({"action": {"$in": ["DELETE_COMPLAINT", "REOPEN_COMPLAINT", "EXTEND_DEADLINE"]}})


def _create_complaint(token: str, title: str = "TEST_LIFECYCLE_COMPLAINT") -> str:
    """Helper to create a complaint and return its ID."""
    response = client.post(
        "/api/complaints/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "description": "This is a test complaint for lifecycle endpoints.",
            "category": "Infrastructure",
            "region": "Test Region",
            "location": "Test Location",
            "priority": "low"
        }
    )
    if response.status_code != 201:
        print(f"Complaint creation failed: {response.text}")
    assert response.status_code == 201
    
    data = response.json()["data"]
    # Handle either _id or id depending on the specific endpoint implementation
    return data.get("id") or data.get("_id")


def test_soft_delete_citizen_success():
    citizen_token = get_token(CITIZEN_EMAIL, CITIZEN_PASS)
    complaint_id = _create_complaint(citizen_token, "TEST_LIFECYCLE_1")

    # Citizen deletes it while it's in 'submitted' status
    response = client.delete(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Verify it is hidden from lists
    list_response = client.get(
        "/api/complaints/",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    ids = [c["id"] for c in list_response.json()["data"]]
    assert complaint_id not in ids

    # Ensure admin can still fetch it directly
    admin_token = get_token(ADMIN_EMAIL, ADMIN_PASS)
    admin_fetch = client.get(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_fetch.status_code == 200
    assert admin_fetch.json()["data"]["is_deleted"] is True


def test_soft_delete_citizen_fail_not_submitted():
    citizen_token = get_token(CITIZEN_EMAIL, CITIZEN_PASS)
    admin_token = get_token(ADMIN_EMAIL, ADMIN_PASS)
    complaint_id = _create_complaint(citizen_token, "TEST_LIFECYCLE_2")

    # Admin changes status to 'under_review'
    client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"status": "under_review"}
    )

    # Citizen attempts deletion and fails
    response = client.delete(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert response.status_code == 400
    res_json = response.json()
    error_msg = res_json.get("error", {}).get("message", "")
    assert "only delete complaints in 'submitted'" in error_msg

    # Admin can still override and delete it
    admin_delete = client.delete(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_delete.status_code == 200


def test_reopen_complaint_success():
    citizen_token = get_token(CITIZEN_EMAIL, CITIZEN_PASS)
    admin_token = get_token(ADMIN_EMAIL, ADMIN_PASS)
    complaint_id = _create_complaint(citizen_token, "TEST_LIFECYCLE_3")

    # Setup: Admin resolves complaint
    client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"status": "resolved"}
    )

    # Citizen reopens complaint
    reopen_res = client.post(
        f"/api/complaints/{complaint_id}/reopen",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"reason": "Test reason"}
    )
    assert reopen_res.status_code == 200

    # Verify state
    fetch = client.get(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    data = fetch.json()["data"]
    assert data["status"] == "reopened"
    assert data["reopen_count"] == 1

    # Verify that updating a reopened complaint works!
    # Update status to 'in_progress'
    update_res = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"status": "in_progress"}
    )
    assert update_res.status_code == 200

    # Verify that it is in_progress
    fetch = client.get(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert fetch.json()["data"]["status"] == "in_progress"

    # Update status to 'resolved'
    update_res = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"status": "resolved"}
    )
    assert update_res.status_code == 200


def test_reopen_complaint_fail_deleted():
    citizen_token = get_token(CITIZEN_EMAIL, CITIZEN_PASS)
    admin_token = get_token(ADMIN_EMAIL, ADMIN_PASS)
    complaint_id = _create_complaint(citizen_token, "TEST_LIFECYCLE_4")

    # Setup: Admin resolves, then soft-deletes complaint
    client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"status": "resolved"}
    )
    client.delete(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Citizen tries to reopen it
    reopen_res = client.post(
        f"/api/complaints/{complaint_id}/reopen",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"reason": "Test reason"}
    )
    # Should throw 400 or 404 (because is_deleted check in reopen throws ValidationError)
    assert reopen_res.status_code in [400, 404]


def test_extend_deadline_success():
    citizen_token = get_token(CITIZEN_EMAIL, CITIZEN_PASS)
    admin_token = get_token(ADMIN_EMAIL, ADMIN_PASS)
    complaint_id = _create_complaint(citizen_token, "TEST_LIFECYCLE_5")
    
    # Directly set a current deadline via db so we can test extending it
    now = datetime.datetime.now(datetime.timezone.utc)
    original_deadline = (now + datetime.timedelta(days=1)).isoformat()
    db.get_collection("complaints").update_one(
        {"id": complaint_id}, 
        {"$set": {"sla_deadline": original_deadline}}
    )

    new_deadline = (now + datetime.timedelta(days=3)).isoformat()

    # Admin extends deadline
    res = client.post(
        f"/api/complaints/{complaint_id}/extend-deadline",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_due_date": new_deadline, "reason": "Requires more time"}
    )
    assert res.status_code == 200

    # Verify history
    fetch = client.get(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    data = fetch.json()["data"]
    assert data["sla_deadline"] == new_deadline
    assert len(data["extension_history"]) == 1
    assert data["extension_history"][0]["reason"] == "Requires more time"

def test_audit_logs_created():
    # Verify audit logs were captured
    logs = list(db.get_collection("audit_logs").find({"action": {"$in": ["DELETE_COMPLAINT", "REOPEN_COMPLAINT", "EXTEND_DEADLINE"]}}))
    assert len(logs) >= 3 # We've performed all 3 successfully and unsuccessfully
