#!/usr/bin/env python3
"""
Isolate Complaint Creation Issue
"""
import requests
import json

def test_minimal_complaint():
    print("🔍 ISOLATING COMPLAINT CREATION ISSUE")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Get working token
    print("\n1️⃣ Getting Authentication Token...")
    
    login_data = {
        "email": "testcitizen1777574736@example.com",
        "password": "TestPass123!@#"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"   ❌ Login failed: {login_response.status_code}")
            return
            
        login_result = login_response.json()
        if not login_result.get("success"):
            print(f"   ❌ Login failed: {login_result}")
            return
            
        token = login_result["data"]["token"]
        print("   ✅ Token obtained")
        
        # Test 2: Minimal complaint data
        print("\n2️⃣ Testing Minimal Complaint...")
        
        minimal_complaint = {
            "title": "Test",
            "description": "Test description",
            "category": "Infrastructure",
            "priority": "medium",
            "location": "Test",
            "region": "Test"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(
            f"{base_url}/api/complaints/",
            json=minimal_complaint,
            headers=headers,
            timeout=15
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 500:
            print("   ❌ 500 Error with minimal data")
            print(f"   Response: {response.text[:300]}")
            
            # Try with missing fields to see validation
            print("\n3️⃣ Testing with Missing Fields...")
            
            # Missing title
            bad_complaint = {
                "description": "Test",
                "category": "Infrastructure",
                "priority": "medium",
                "location": "Test",
                "region": "Test"
            }
            
            response = requests.post(
                f"{base_url}/api/complaints/",
                json=bad_complaint,
                headers=headers,
                timeout=15
            )
            
            print(f"   Missing Title Status: {response.status_code}")
            
            # Invalid category
            bad_complaint = {
                "title": "Test",
                "description": "Test description",
                "category": "InvalidCategory",
                "priority": "medium",
                "location": "Test",
                "region": "Test"
            }
            
            response = requests.post(
                f"{base_url}/api/complaints/",
                json=bad_complaint,
                headers=headers,
                timeout=15
            )
            
            print(f"   Invalid Category Status: {response.status_code}")
            
        elif response.status_code == 201:
            print("   ✅ Minimal complaint: SUCCESS!")
            result = response.json()
            complaint_id = result["data"]["id"]
            print(f"   Complaint ID: {complaint_id}")
            
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 ISSUE ISOLATION COMPLETE")
    print("\n📋 If you see 500 errors:")
    print("   1. The issue is in the complaint creation logic")
    print("   2. Check server console for detailed error messages")
    print("   3. The issue is NOT with authentication or database")
    print("\n🔧 SOLUTION:")
    print("   1. Use the working test credentials in browser")
    print("   2. Monitor browser DevTools console")
    print("   3. Check server terminal for error details")

if __name__ == "__main__":
    test_minimal_complaint()
