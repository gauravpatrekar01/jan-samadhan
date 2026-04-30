#!/usr/bin/env python3
"""
Quick Fix for Token Issues
"""
import requests
import json

def test_working_login():
    print("🔧 Quick Fix for Token Issues")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️ Server status: {response.status_code}")
    except:
        print("❌ Server not reachable")
        return
    
    print("\n🎯 SOLUTION: Fresh Login")
    print("Since token refresh has issues, let's get fresh tokens:")
    
    # Test with a sample login (you'll need real credentials)
    print("\n1. Open your browser and go to: http://localhost:3000/index.html")
    print("2. Login with your credentials")
    print("3. Check browser console for token storage")
    print("4. Try creating a complaint")
    
    print("\n🔍 After Login, Check Browser Console:")
    print("   Open DevTools → Console")
    print("   Type: localStorage.getItem('js_user')")
    print("   You should see: {token: '...', refresh_token: '...'}")
    
    print("\n📋 Manual Token Test:")
    print("   If you have a valid token, test it with:")
    print("   curl -H 'Authorization: Bearer YOUR_TOKEN' http://localhost:8000/api/complaints/")
    
    print("\n🚀 Enhanced Features Available After Login:")
    print("   • Media Upload: POST /api/complaints/with-media")
    print("   • Social Features: POST /api/complaints/{id}/vote")
    print("   • Predictions: GET /api/analytics/predictions")
    print("   • Public Dashboard: GET /api/public/stats")
    
    print("\n📝 If Issues Persist:")
    print("   1. Clear browser cache and cookies")
    print("   2. Try incognito/private window")
    print("   3. Check server logs for errors")
    print("   4. Verify .env has correct values")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_working_login()
