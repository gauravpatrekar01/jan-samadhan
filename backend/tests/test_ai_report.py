import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime, timezone

# Add the backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.dirname(__file__))

from limiter import limiter
limiter.enabled = False

from app import app
from db import db
from security import create_access_token

client = TestClient(app)

CITIZEN_EMAIL = "citizen@example.com"
CITIZEN_PASS = "CitizenSecure123!"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASS = "AdminSecure123!"
OFFICER_EMAIL = "officer@gov.in"
OFFICER_PASS = "OfficerSecure123!"

_TOKEN_CACHE = {}

def get_token(email, password):
    if email in _TOKEN_CACHE:
        return _TOKEN_CACHE[email]
        
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        response = client.post("/api/auth/admin-login", json={"email": email, "password": password})
        
    token = response.json()["data"]["token"]
    _TOKEN_CACHE[email] = token
    return token


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Clean up any complaints and audit logs created during testing."""
    db.get_collection("complaints").delete_many({"title": {"$regex": "^TEST_AI_REPORT"}})
    yield
    db.get_collection("complaints").delete_many({"title": {"$regex": "^TEST_AI_REPORT"}})
    db.get_collection("audit_logs").delete_many({"action": "AI_REPORT_GENERATED"})


def _create_complaint(token: str, title: str) -> str:
    """Helper to create a complaint."""
    response = client.post(
        "/api/complaints/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "description": "This is a billing irregularity and possible financial mismanagement in Raigad government hospital affecting public healthcare.",
            "category": "Healthcare",
            "region": "Raigad",
            "location": "Government Hospital",
            "priority": "high"
        }
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_ai_report_generation_and_caching():
    citizen_token = get_token(CITIZEN_EMAIL, CITIZEN_PASS)
    admin_token = get_token(ADMIN_EMAIL, ADMIN_PASS)
    
    # 1. Create complaint as citizen
    complaint_id = _create_complaint(citizen_token, "TEST_AI_REPORT_GEN")
    
    # 2. Generate report as admin (POST)
    gen_response = client.post(
        f"/api/complaints/{complaint_id}/ai-report/generate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert gen_response.status_code == 200
    report = gen_response.json()["data"]
    
    # Validate report schema and keys
    assert report["complaint_id"] == complaint_id
    assert "summary_insight" in report
    assert isinstance(report["severity_score"], int)
    assert report["urgency_level"] in ["low", "medium", "high", "critical"]
    assert "risk_flags" in report
    assert "fraud_risk" in report["risk_flags"]
    assert "mismanagement_risk" in report["risk_flags"]
    assert "escalation_risk" in report["risk_flags"]
    assert "category_validation" in report
    assert report["category_validation"]["user_category"] == "Healthcare"
    assert "ai_predicted_category" in report["category_validation"]
    assert "sentiment" in report
    assert "recommended_department" in report
    assert isinstance(report["suggested_actions"], list)
    assert "entity_extraction" in report
    assert "location" in report["entity_extraction"]
    assert "keywords" in report["entity_extraction"]
    assert "organizations" in report["entity_extraction"]
    assert "generated_at" in report
    assert report["version"] == "v1"
    
    # 3. Retrieve report via GET as citizen (owner)
    get_response = client.get(
        f"/api/complaints/{complaint_id}/ai-report",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert get_response.status_code == 200
    retrieved = get_response.json()["data"]
    assert retrieved["generated_at"] == report["generated_at"]  # Verify cached report was returned
    
    # 4. Refresh report via GET with refresh=true
    refresh_response = client.get(
        f"/api/complaints/{complaint_id}/ai-report",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"refresh": "true"}
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()["data"]
    assert "summary_insight" in refreshed


def test_ai_report_security_authorization():
    citizen1_token = get_token(CITIZEN_EMAIL, CITIZEN_PASS)
    
    # Generate second citizen token dynamically
    citizen2_token = create_access_token({"sub": "citizen2@example.com", "role": "citizen"})
    
    # Citizen 1 creates the complaint
    complaint_id = _create_complaint(citizen1_token, "TEST_AI_REPORT_SECURITY")
    
    # Citizen 2 tries to retrieve citizen 1's complaint AI report -> should return 403 Forbidden
    response = client.get(
        f"/api/complaints/{complaint_id}/ai-report",
        headers={"Authorization": f"Bearer {citizen2_token}"}
    )
    assert response.status_code == 403
    
    # Citizen 2 tries to generate report for citizen 1's complaint -> should return 403 Forbidden
    response = client.post(
        f"/api/complaints/{complaint_id}/ai-report/generate",
        headers={"Authorization": f"Bearer {citizen2_token}"}
    )
    assert response.status_code == 403


def test_ai_report_audit_logging():
    citizen_token = get_token(CITIZEN_EMAIL, CITIZEN_PASS)
    admin_token = get_token(ADMIN_EMAIL, ADMIN_PASS)
    
    # Create complaint as citizen
    complaint_id = _create_complaint(citizen_token, "TEST_AI_REPORT_AUDIT")
    
    # Generate report as admin
    gen_response = client.post(
        f"/api/complaints/{complaint_id}/ai-report/generate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert gen_response.status_code == 200
    report = gen_response.json()["data"]
    
    # Query database directly for the audit log
    audit_logs = list(db.get_collection("audit_logs").find({
        "action": "AI_REPORT_GENERATED",
        "resource_id": complaint_id
    }))
    
    assert len(audit_logs) >= 1
    log = audit_logs[0]
    assert log["actor_email"] == ADMIN_EMAIL
    assert "details" in log
    assert log["details"]["severity_score"] == report["severity_score"]
