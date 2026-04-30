#!/usr/bin/env python
"""
Direct API test to debug complaint submission issues
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test credentials (these should exist from create_test_users.py)
TEST_CITIZEN = {
    "email": "citizen@example.com",
    "password": "CitizenSecure123!"
}

def test_complaint_flow():
    """Test the complete complaint submission flow"""
    
    session = requests.Session()
    
    # Step 1: Login
    print("\n📍 Step 1: Testing Login...")
    login_response = session.post(
        f"{BASE_URL}/api/auth/login",
        json=TEST_CITIZEN
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    print(f"✅ Login successful")
    print(f"   User role: {login_data.get('data', {}).get('role')}")
    print(f"   Token: {login_data.get('data', {}).get('token')[:50]}...")
    
    token = login_data.get('data', {}).get('token')
    if not token:
        print("❌ No token in login response!")
        return False
    
    # Step 2: Create complaint
    print("\n📍 Step 2: Testing Complaint Submission...")
    
    complaint_data = {
        "title": "Potholes on Main Road",
        "description": "There are large potholes on Main Street that are causing traffic issues and damaging vehicles.",
        "category": "Infrastructure",
        "subcategory": "Road Maintenance",
        "priority": "high",
        "location": "Main Street, Downtown",
        "region": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n📤 Sending complaint data:")
    print(json.dumps(complaint_data, indent=2))
    
    complaint_response = session.post(
        f"{BASE_URL}/api/complaints/",
        json=complaint_data,
        headers=headers
    )
    
    print(f"\n📥 Response Status: {complaint_response.status_code}")
    
    if complaint_response.status_code != 201:
        print(f"❌ Complaint submission failed!")
        print(f"Response: {complaint_response.text}")
        
        # Try to parse error details
        try:
            error_data = complaint_response.json()
            print(f"\n📋 Error Details:")
            print(json.dumps(error_data, indent=2))
        except:
            pass
        
        return False
    
    response_data = complaint_response.json()
    print(f"✅ Complaint submission successful!")
    print(f"\n📋 Response Data:")
    print(json.dumps(response_data, indent=2))
    
    complaint_id = response_data.get('data', {}).get('id')
    print(f"\n🎉 Complaint ID: {complaint_id}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 JanSamadhan Complaint Submission Test")
    print("=" * 60)
    
    success = test_complaint_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Test failed - see details above")
    print("=" * 60)
