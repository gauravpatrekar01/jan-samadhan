#!/usr/bin/env python3
"""
Test Authentication Bug Fix
"""
import requests
import json
import time

def test_auth_fix():
    print("🔧 TESTING AUTHENTICATION BUG FIX")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Valid login
    print("\n1️⃣ Testing Valid Login...")
    
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
        
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get("success"):
                token = login_result["data"]["token"]
                refresh_token = login_result["data"]["refresh_token"]
                print("   ✅ Login successful")
                print(f"   Token: {token[:30]}...")
                print(f"   Refresh Token: {refresh_token[:30]}...")
            else:
                print(f"   ❌ Login failed: {login_result}")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return
    
    # Test 2: Test with valid token
    print("\n2️⃣ Testing Valid Token...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        user_response = requests.get(
            f"{base_url}/api/auth/user",
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {user_response.status_code}")
        
        if user_response.status_code == 200:
            print("   ✅ Valid token works")
        else:
            print(f"   ❌ Valid token failed: {user_response.status_code}")
            print(f"   Response: {user_response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Valid token error: {e}")
    
    # Test 3: Test with invalid token format
    print("\n3️⃣ Testing Invalid Token Format...")
    
    try:
        headers = {"Authorization": "Bearer invalid_token_format"}
        user_response = requests.get(
            f"{base_url}/api/auth/user",
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {user_response.status_code}")
        
        if user_response.status_code == 401:
            result = user_response.json()
            if result.get("error", {}).get("code") == "TOKEN_INVALID":
                print("   ✅ Invalid token properly rejected")
            else:
                print(f"   ❌ Wrong error code: {result}")
        else:
            print(f"   ❌ Unexpected status: {user_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Invalid token error: {e}")
    
    # Test 4: Test with missing token
    print("\n4️⃣ Testing Missing Token...")
    
    try:
        user_response = requests.get(
            f"{base_url}/api/auth/user",
            timeout=10
        )
        
        print(f"   Status: {user_response.status_code}")
        
        if user_response.status_code == 401:
            result = user_response.json()
            if result.get("error", {}).get("code") == "TOKEN_MISSING":
                print("   ✅ Missing token properly handled")
            else:
                print(f"   ❌ Wrong error code: {result}")
        else:
            print(f"   ❌ Unexpected status: {user_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Missing token error: {e}")
    
    # Test 5: Test refresh with valid token
    print("\n5️⃣ Testing Refresh with Valid Token...")
    
    try:
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = requests.post(
            f"{base_url}/api/auth/refresh",
            json=refresh_data,
            timeout=10
        )
        
        print(f"   Status: {refresh_response.status_code}")
        
        if refresh_response.status_code == 200:
            result = refresh_response.json()
            if result.get("success"):
                print("   ✅ Refresh successful")
            else:
                print(f"   ❌ Refresh failed: {result}")
        else:
            print(f"   ❌ Refresh failed: {refresh_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Refresh error: {e}")
    
    # Test 6: Test refresh with invalid token
    print("\n6️⃣ Testing Refresh with Invalid Token...")
    
    try:
        refresh_data = {"refresh_token": "invalid.jwt.token"}
        refresh_response = requests.post(
            f"{base_url}/api/auth/refresh",
            json=refresh_data,
            timeout=10
        )
        
        print(f"   Status: {refresh_response.status_code}")
        
        if refresh_response.status_code == 401:
            result = refresh_response.json()
            if result.get("error", {}).get("code") == "REFRESH_TOKEN_INVALID":
                print("   ✅ Invalid refresh token properly rejected")
            else:
                print(f"   ❌ Wrong error code: {result}")
        else:
            print(f"   ❌ Unexpected status: {refresh_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Invalid refresh error: {e}")
    
    # Test 7: Test refresh with missing token
    print("\n7️⃣ Testing Refresh with Missing Token...")
    
    try:
        refresh_data = {}
        refresh_response = requests.post(
            f"{base_url}/api/auth/refresh",
            json=refresh_data,
            timeout=10
        )
        
        print(f"   Status: {refresh_response.status_code}")
        
        if refresh_response.status_code == 400:
            result = refresh_response.json()
            if result.get("error", {}).get("code") == "REFRESH_TOKEN_MISSING":
                print("   ✅ Missing refresh token properly handled")
            else:
                print(f"   ❌ Wrong error code: {result}")
        else:
            print(f"   ❌ Unexpected status: {refresh_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Missing refresh error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 AUTHENTICATION BUG FIX TEST COMPLETE")
    print("\n📋 EXPECTED RESULTS:")
    print("   • No more TypeError crashes")
    print("   • Proper HTTP 401 responses")
    print("   • Consistent error format")
    print("   • Frontend can handle token refresh")
    
    print("\n✅ FIX SUMMARY:")
    print("   • TokenExpiredError is now simple Exception")
    print("   • All token errors converted to HTTPException")
    print("   • Consistent error response format")
    print("   • Debug logging added")
    print("   • Refresh token validation enhanced")

if __name__ == "__main__":
    test_auth_fix()
