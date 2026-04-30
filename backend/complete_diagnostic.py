#!/usr/bin/env python3
"""
Complete Grievance Submission Diagnostic
"""
import requests
import json
import time

def test_complete_grievance_flow():
    print("🔍 COMPLETE GRIEVANCE SUBMISSION DIAGNOSTIC")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Server Health
    print("\n1️⃣ Testing Server Health...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Server Status: {response.status_code} ✅")
    except Exception as e:
        print(f"   Server Status: ❌ {e}")
        return
    
    # Test 2: Get a fresh token (simulate login)
    print("\n2️⃣ Testing Authentication...")
    
    # First, try to register a test user
    test_user = {
        "name": "Test User",
        "email": f"test{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "role": "citizen"
    }
    
    try:
        # Register test user
        register_response = requests.post(
            f"{base_url}/api/auth/register",
            json=test_user,
            timeout=5
        )
        print(f"   Register Test User: {register_response.status_code}")
        
        # Login with test user
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            },
            timeout=5
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            if login_data.get("success"):
                token = login_data["data"]["token"]
                print(f"   ✅ Login Successful: Token obtained")
                
                # Test 3: Original complaint endpoint
                print("\n3️⃣ Testing Original Complaint Endpoint...")
                complaint_data = {
                    "title": "Test Complaint for Debugging",
                    "description": "This is a test complaint to diagnose submission issues. Please ignore.",
                    "category": "Infrastructure",
                    "priority": "medium",
                    "location": "Test Location",
                    "region": "Test Region",
                    "latitude": 19.0760,
                    "longitude": 72.8777
                }
                
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                complaint_response = requests.post(
                    f"{base_url}/api/complaints/",
                    json=complaint_data,
                    headers=headers,
                    timeout=10
                )
                
                print(f"   Original Endpoint: {complaint_response.status_code}")
                if complaint_response.status_code == 201:
                    print("   ✅ Original complaint endpoint: WORKING")
                else:
                    print(f"   ❌ Original endpoint failed: {complaint_response.text[:200]}...")
                
                # Test 4: Enhanced complaint endpoint (with media)
                print("\n4️⃣ Testing Enhanced Complaint Endpoint...")
                
                # Try without files first
                enhanced_response = requests.post(
                    f"{base_url}/api/complaints/with-media",
                    data=complaint_data,  # Form data
                    headers=headers,
                    timeout=10
                )
                
                print(f"   Enhanced Endpoint: {enhanced_response.status_code}")
                if enhanced_response.status_code == 201:
                    print("   ✅ Enhanced complaint endpoint: WORKING")
                else:
                    print(f"   ❌ Enhanced endpoint failed: {enhanced_response.text[:200]}...")
                
                # Test 5: Social features
                print("\n5️⃣ Testing Social Features...")
                
                # Create a test complaint first to have something to vote on
                test_complaint_response = requests.post(
                    f"{base_url}/api/complaints/",
                    json=complaint_data,
                    headers=headers,
                    timeout=10
                )
                
                if test_complaint_response.status_code == 201:
                    test_complaint = test_complaint_response.json()
                    complaint_id = test_complaint["data"]["id"]
                    
                    # Test voting
                    vote_response = requests.post(
                        f"{base_url}/api/complaints/{complaint_id}/vote?vote_type=up",
                        headers=headers,
                        timeout=5
                    )
                    print(f"   Vote Feature: {vote_response.status_code}")
                    
                    # Test commenting
                    comment_response = requests.post(
                        f"{base_url}/api/complaints/{complaint_id}/comment",
                        data={"comment": "Test comment for debugging"},
                        headers=headers,
                        timeout=5
                    )
                    print(f"   Comment Feature: {comment_response.status_code}")
                
                # Test 6: Public endpoints
                print("\n6️⃣ Testing Public Endpoints...")
                
                stats_response = requests.get(f"{base_url}/api/public/stats", timeout=5)
                print(f"   Public Stats: {stats_response.status_code}")
                
                predictions_response = requests.get(f"{base_url}/api/analytics/predictions", timeout=5)
                print(f"   Predictions: {predictions_response.status_code}")
                
            else:
                print(f"   ❌ Login failed: {login_response.text[:200]}...")
        else:
            print(f"   ❌ Registration failed: {register_response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC COMPLETE")
    print("\n📋 NEXT STEPS:")
    print("1. If all tests pass → Issue is in frontend")
    print("2. If tests fail → Issue is in backend")
    print("3. Check browser console for JavaScript errors")
    print("4. Verify network requests in browser DevTools")
    print("5. Try submitting complaint manually in browser")

if __name__ == "__main__":
    test_complete_grievance_flow()
