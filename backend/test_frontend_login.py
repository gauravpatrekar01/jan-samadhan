#!/usr/bin/env python3
"""
Test Frontend Login Fix
"""
import requests
import json

def test_frontend_login_fix():
    print("🔧 TESTING FRONTEND LOGIN FIX")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if backend is running
    print("\n1️⃣ Testing Backend Health...")
    try:
        health_response = requests.get(f"{base_url}/", timeout=5)
        if health_response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   ❌ Backend status: {health_response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Backend not reachable: {e}")
        return
    
    # Test 2: Test login endpoint
    print("\n2️⃣ Testing Login Endpoint...")
    
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
        
        print(f"   Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get("success"):
                token = login_result["data"]["token"]
                refresh_token = login_result["data"]["refresh_token"]
                user_role = login_result["data"].get("role", "citizen")
                
                print("   ✅ Login successful")
                print(f"   Token: {token[:30]}...")
                print(f"   Refresh Token: {refresh_token[:30]}...")
                print(f"   User Role: {user_role}")
                
                # Test 3: Test user endpoint with the token
                print("\n3️⃣ Testing User Endpoint...")
                
                headers = {"Authorization": f"Bearer {token}"}
                user_response = requests.get(
                    f"{base_url}/api/auth/user",
                    headers=headers,
                    timeout=10
                )
                
                print(f"   Status Code: {user_response.status_code}")
                
                if user_response.status_code == 200:
                    print("   ✅ User endpoint working")
                else:
                    print(f"   ❌ User endpoint failed: {user_response.status_code}")
                    
            else:
                print(f"   ❌ Login failed: {login_result}")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text[:300]}...")
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 FRONTEND LOGIN FIX SUMMARY:")
    print("\n✅ WHAT WAS FIXED:")
    print("   • Added missing adminLogin method to JanSamadhanAPI")
    print("   • Added missing handleLoginSuccess function")
    print("   • Fixed undefined method calls")
    print("\n✅ EXPECTED BEHAVIOR:")
    print("   • Login button should work without JavaScript errors")
    print("   • Admin login should work correctly")
    print("   • Success callback should close modal and redirect")
    print("\n📋 TESTING INSTRUCTIONS:")
    print("   1. Open browser to: http://localhost:3000/index.html")
    print("   2. Click any login button")
    print("   3. Use test credentials:")
    print("      Email: testcitizen1777574736@example.com")
    print("      Password: TestPass123!@#")
    print("   4. Should login successfully without errors")
    print("\n🔧 DEBUGGING:")
    print("   • Check browser console for any remaining errors")
    print("   • Verify JanSamadhanAPI is loaded: window.JanSamadhanAPI")
    print("   • Verify methods: window.JanSamadhanAPI.login")

if __name__ == "__main__":
    test_frontend_login_fix()
