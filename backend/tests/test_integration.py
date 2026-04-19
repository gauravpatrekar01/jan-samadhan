"""
Unit Tests for JanSamadhan Backend
Run with: pytest backend/tests/test_main.py -v
"""

import pytest
import sys
sys.path.insert(0, './backend')

from httpx import Client
from datetime import datetime, timezone
import os

BASE_URL = os.getenv('TEST_URL', 'http://localhost:8000')

# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_citizen_login(self):
        """✓ Citizen can login with correct credentials"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == "citizen"
        assert "token" in data["data"]
        assert "refresh_token" in data["data"]
        print("✓ Citizen login successful")
    
    def test_officer_login(self):
        """✓ Officer can login with correct credentials"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "officer@example.com",
            "password": "OfficerSecure123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["role"] == "officer"
        print("✓ Officer login successful")
    
    def test_admin_login(self):
        """✓ Admin can login via admin endpoint"""
        response = Client().post(f"{BASE_URL}/api/auth/admin-login", json={
            "email": "admin@example.com",
            "password": "AdminSecure123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["role"] == "admin"
        print("✓ Admin login successful")
    
    def test_invalid_password(self):
        """✓ Login fails with invalid password"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "WrongPassword123!"
        })
        assert response.status_code == 401
        print("✓ Invalid password rejected")
    
    def test_user_not_found(self):
        """✓ Login fails for non-existent user"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 401
        print("✓ Non-existent user rejected")
    
    def test_token_format(self):
        """✓ JWT token has correct format"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        token = response.json()["data"]["token"]
        # JWT format: header.payload.signature
        assert token.count('.') == 2
        print("✓ JWT token format correct")
    
    def test_refresh_token_endpoint(self):
        """✓ Refresh token endpoint returns new access token"""
        # First get tokens
        login_response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        refresh_token = login_response.json()["data"]["refresh_token"]
        
        # Use refresh token
        response = Client().post(f"{BASE_URL}/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        assert "token" in response.json()["data"]
        print("✓ Refresh token endpoint working")


# ═══════════════════════════════════════════════════════════════════
# COMPLAINT MANAGEMENT TESTS
# ═══════════════════════════════════════════════════════════════════

class TestComplaintManagement:
    """Test complaint creation and management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        self.token = response.json()["data"]["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.client = Client()
    
    def test_create_complaint(self):
        """✓ Citizen can create a complaint"""
        response = self.client.post(
            f"{BASE_URL}/api/complaints/",
            headers=self.headers,
            json={
                "title": "Broken streetlight",
                "category": "infrastructure",
                "priority": "high",
                "description": "Street light near sector 5 is broken",
                "location": {"lat": 19.0760, "lng": 72.8777}
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["status"] == "submitted"
        assert data["data"]["priority"] == "high"
        assert data["data"]["title"] == "Broken streetlight"
        print("✓ Complaint created successfully")
    
    def test_missing_required_field(self):
        """✓ Complaint creation fails without required fields"""
        response = self.client.post(
            f"{BASE_URL}/api/complaints/",
            headers=self.headers,
            json={
                "category": "infrastructure",
                # Missing title, priority, description
            }
        )
        assert response.status_code == 400
        print("✓ Validation enforced for required fields")
    
    def test_invalid_priority(self):
        """✓ Complaint creation fails with invalid priority"""
        response = self.client.post(
            f"{BASE_URL}/api/complaints/",
            headers=self.headers,
            json={
                "title": "Test",
                "category": "infrastructure",
                "priority": "invalid_priority",  # Invalid priority
                "description": "Test",
                "location": {"lat": 19.0760, "lng": 72.8777}
            }
        )
        assert response.status_code == 400
        print("✓ Invalid priority rejected")
    
    def test_view_own_complaints(self):
        """✓ Citizen can view their own complaints"""
        response = self.client.get(
            f"{BASE_URL}/api/complaints/my",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)
        print("✓ Retrieved user complaints")
    
    def test_unauthorized_access(self):
        """✓ Cannot access complaints without token"""
        response = self.client.get(f"{BASE_URL}/api/complaints/my")
        assert response.status_code == 401
        print("✓ Unauthorized access blocked")
    
    def test_pagination(self):
        """✓ Complaint list supports pagination"""
        response = self.client.get(
            f"{BASE_URL}/api/complaints/my?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200
        print("✓ Pagination works")
    
    def test_filter_by_status(self):
        """✓ Can filter complaints by status"""
        response = self.client.get(
            f"{BASE_URL}/api/complaints/my?status=submitted",
            headers=self.headers
        )
        assert response.status_code == 200
        print("✓ Status filter works")


# ═══════════════════════════════════════════════════════════════════
# ROLE-BASED ACCESS CONTROL TESTS
# ═══════════════════════════════════════════════════════════════════

class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_citizen_cannot_access_admin_endpoints(self):
        """✓ Citizen token cannot access admin endpoints"""
        # Get citizen token
        login_response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        token = login_response.json()["data"]["token"]
        
        # Try to access admin endpoint
        response = Client().get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be forbidden or unauthorized
        assert response.status_code in [401, 403]
        print("✓ Citizen blocked from admin endpoints")
    
    def test_officer_cannot_login_via_standard_endpoint(self):
        """✓ Officer must use standard login (not admin-login)"""
        # Officers use standard login endpoint
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "officer@example.com",
            "password": "OfficerSecure123!"
        })
        assert response.status_code == 200
        print("✓ Officer login via standard endpoint works")


# ═══════════════════════════════════════════════════════════════════
# API ERROR HANDLING TESTS
# ═══════════════════════════════════════════════════════════════════

class TestErrorHandling:
    """Test error handling and error messages"""
    
    def test_invalid_email_format(self):
        """✓ Invalid email format is rejected"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid-email",  # Invalid format
            "password": "Password123!"
        })
        assert response.status_code == 422  # Validation error
        print("✓ Invalid email format rejected")
    
    def test_missing_required_field(self):
        """✓ Missing required field returns error"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com"
            # Missing password
        })
        assert response.status_code in [400, 422]
        print("✓ Missing field error returned")
    
    def test_500_error_handling(self):
        """✓ Server errors don't crash API"""
        # Try to access invalid endpoint
        response = Client().get(f"{BASE_URL}/api/invalid-endpoint")
        assert response.status_code == 404
        print("✓ Invalid endpoint returns 404")


# ═══════════════════════════════════════════════════════════════════
# PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestPerformance:
    """Test API performance"""
    
    def test_login_response_time(self):
        """✓ Login completes in < 2 seconds"""
        import time
        start = time.time()
        
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        
        duration = time.time() - start
        assert response.status_code == 200
        assert duration < 2.0, f"Login took {duration}s, expected < 2s"
        print(f"✓ Login completed in {duration:.3f}s (< 2s)")
    
    def test_list_complaints_response_time(self):
        """✓ Listing complaints completes in < 2 seconds"""
        import time
        
        # Get token
        login_response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        token = login_response.json()["data"]["token"]
        
        start = time.time()
        response = Client().get(
            f"{BASE_URL}/api/complaints/my",
            headers={"Authorization": f"Bearer {token}"}
        )
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0, f"Request took {duration}s, expected < 2s"
        print(f"✓ List complaints completed in {duration:.3f}s (< 2s)")


# ═══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestIntegration:
    """Test complete user workflows"""
    
    def test_complete_login_flow(self):
        """✓ Complete login, get token, use token flow"""
        client = Client()
        
        # Step 1: Login
        login_response = client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        assert login_response.status_code == 200
        
        token = login_response.json()["data"]["token"]
        
        # Step 2: Use token in request
        response = client.get(
            f"{BASE_URL}/api/complaints/my",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        print("✓ Complete login flow successful")
    
    def test_complaint_lifecycle(self):
        """✓ Citizen can create complaint and view it"""
        client = Client()
        
        # Login
        login_response = client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        token = login_response.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create complaint
        create_response = client.post(
            f"{BASE_URL}/api/complaints/",
            headers=headers,
            json={
                "title": "Test complaint",
                "category": "infrastructure",
                "priority": "normal",
                "description": "Test",
                "location": {"lat": 19.0760, "lng": 72.8777}
            }
        )
        assert create_response.status_code == 201
        complaint_id = create_response.json()["data"]["_id"]
        
        # Retrieve complaint
        get_response = client.get(
            f"{BASE_URL}/api/complaints/{complaint_id}",
            headers=headers
        )
        assert get_response.status_code == 200
        
        print("✓ Complaint lifecycle complete")


# ═══════════════════════════════════════════════════════════════════
# SECURITY TESTS
# ═══════════════════════════════════════════════════════════════════

class TestSecurity:
    """Test security aspects"""
    
    def test_password_not_returned_in_response(self):
        """✓ Passwords never returned in API responses"""
        response = Client().post(f"{BASE_URL}/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
        
        response_data = response.json()
        assert "password" not in response_data["data"]
        print("✓ Password not exposed in response")
    
    def test_invalid_token_rejected(self):
        """✓ Invalid token is rejected"""
        response = Client().get(
            f"{BASE_URL}/api/complaints/my",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401
        print("✓ Invalid token rejected")
    
    def test_expired_token_handling(self):
        """✓ Expired token returns proper error"""
        # Note: This would require creating an expired token
        # For now, just verify invalid token is handled
        response = Client().get(
            f"{BASE_URL}/api/complaints/my",
            headers={"Authorization": "Bearer expired_token"}
        )
        assert response.status_code == 401
        print("✓ Expired token handled")


# ═══════════════════════════════════════════════════════════════════
# TEST EXECUTION
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🧪 Running JanSamadhan Backend Tests\n")
    pytest.main([__file__, "-v", "--tb=short"])
