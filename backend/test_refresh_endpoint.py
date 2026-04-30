#!/usr/bin/env python3
"""
Test Token Refresh Endpoint
"""
import requests
import json

def test_refresh_endpoint():
    print("🔄 Testing Token Refresh Endpoint")
    print("=" * 50)
    
    # Test refresh endpoint health
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/refresh",
            json={"refresh_token": "test_token"},
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint responding: {data.get('success', False)}")
        elif response.status_code == 400:
            print("⚠️ Invalid refresh token (expected)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not reachable")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🔍 Testing Login Endpoint")
    
    # Test login endpoint
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "test_password"
            },
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                user_data = data.get('data', {})
                print(f"✅ Login working")
                print(f"   Token: {user_data.get('token', '')[:20]}...")
                print(f"   Refresh Token: {user_data.get('refresh_token', '')[:20]}...")
            else:
                print("⚠️ Login failed")
        else:
            print(f"❌ Login error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Login test error: {e}")
    
    print("\n" + "=" * 50)
    print("💡 If refresh endpoint works, issue is in frontend token handling")
    print("💡 If login works, you can get fresh tokens by logging in again")

if __name__ == "__main__":
    test_refresh_endpoint()
