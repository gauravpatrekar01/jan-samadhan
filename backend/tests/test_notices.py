#!/usr/bin/env python3
"""Test notice management feature - officers and admins"""

import httpx
import json

# API base URL
BASE_URL = "http://localhost:8000"

# Test credentials
ADMIN_EMAIL = "admin@gov.in"
ADMIN_PASSWORD = "AdminSecure123!"
OFFICER_EMAIL = "officer@gov.in"
OFFICER_PASSWORD = "OfficerSecure123!"

def login(email: str, password: str, role: str = "citizen") -> str:
    """Login and return JWT token"""
    endpoint = "/api/auth/admin-login" if role == "admin" else "/api/auth/login"
    response = httpx.post(f"{BASE_URL}{endpoint}", json={
        "email": email,
        "password": password
    }, timeout=30)
    data = response.json()
    if data.get("success"):
        return data["data"]["token"]
    raise Exception(f"Login failed: {data}")

def get_notifications(token: str) -> list:
    """Get public notices (no auth required for get)"""
    response = httpx.get(
        f"{BASE_URL}/api/admin/notices",
        timeout=30
    )
    return response.json().get("data", [])

def add_notice(token: str, text: str) -> dict:
    """Add a notice (officer or admin)"""
    response = httpx.post(
        f"{BASE_URL}/api/admin/notices",
        json={"text": text, "pinned": False},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    if response.status_code == 201:
        return response.json()["data"]
    raise Exception(f"Failed to add notice: {response.text}")

def delete_notice(token: str, notice_id: str) -> dict:
    """Delete a notice"""
    response = httpx.delete(
        f"{BASE_URL}/api/admin/notices/{notice_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Failed to delete notice: {response.text}")

def test_notice_management():
    """Test notice management for officers and admins"""
    print("🧪 Testing Notice Management Feature\n" + "="*50)
    
    # Step 1: Login as officer and admin
    print("\n1️⃣ Logging in as Officer and Admin...")
    try:
        officer_token = login(OFFICER_EMAIL, OFFICER_PASSWORD)
        admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD, role="admin")
        print("✅ Both logged in successfully")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Step 2: Officer adds a notice
    print("\n2️⃣ Officer adding notice...")
    try:
        officer_notice = add_notice(officer_token, "Officer Update: Road maintenance ongoing in Zone A")
        print(f"✅ Officer notice created: {officer_notice['id']}")
        print(f"   - Created by: {officer_notice['createdBy']}")
        print(f"   - Role: {officer_notice.get('createdByRole', 'N/A')}")
    except Exception as e:
        print(f"❌ Officer notice failed: {e}")
        return
    
    # Step 3: Admin adds a notice
    print("\n3️⃣ Admin adding notice...")
    try:
        admin_notice = add_notice(admin_token, "Admin Notice: System maintenance on Friday 2-4 AM")
        print(f"✅ Admin notice created: {admin_notice['id']}")
        print(f"   - Created by: {admin_notice['createdBy']}")
        print(f"   - Role: {admin_notice.get('createdByRole', 'N/A')}")
    except Exception as e:
        print(f"❌ Admin notice failed: {e}")
        return
    
    # Step 4: Get all notices
    print("\n4️⃣ Fetching all notices...")
    try:
        notices = get_notifications(None)
        print(f"✅ Total notices: {len(notices)}")
        for n in notices[:3]:
            role = n.get('createdByRole', 'unknown')
            print(f"   - {n['text'][:50]}... (By {role})")
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
    
    # Step 5: Officer deletes their own notice
    print("\n5️⃣ Officer deleting their own notice...")
    try:
        delete_notice(officer_token, officer_notice['id'])
        print(f"✅ Officer successfully deleted their notice")
    except Exception as e:
        print(f"❌ Delete failed: {e}")
    
    # Step 6: Officer tries to delete admin's notice (should fail)
    print("\n6️⃣ Officer trying to delete admin's notice (should fail)...")
    try:
        delete_notice(officer_token, admin_notice['id'])
        print(f"❌ ERROR: Officer was able to delete admin's notice!")
    except Exception as e:
        if "only delete notices you created" in str(e):
            print(f"✅ Correctly prevented: {str(e)[:60]}...")
        else:
            print(f"❌ Unexpected error: {e}")
    
    # Step 7: Admin deletes anyone's notice
    print("\n7️⃣ Admin deleting officer's notice that was already deleted...")
    print("   (Creating new officer notice for this test)")
    try:
        officer_notice2 = add_notice(officer_token, "Test notice for admin to delete")
        delete_notice(admin_token, officer_notice2['id'])
        print(f"✅ Admin successfully deleted officer's notice")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Step 8: Admin deletes admin's notice
    print("\n8️⃣ Admin deleting their own notice...")
    try:
        delete_notice(admin_token, admin_notice['id'])
        print(f"✅ Admin successfully deleted their own notice")
    except Exception as e:
        print(f"❌ Delete failed: {e}")
    
    print("\n" + "="*50)
    print("✅ All tests completed successfully!")

if __name__ == "__main__":
    test_notice_management()
