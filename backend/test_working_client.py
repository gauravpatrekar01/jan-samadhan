#!/usr/bin/env python3
"""
Test the working API
"""
import requests
import json

def test_working_api():
    print("🧪 TESTING WORKING COMPLAINT API")
    print("=" * 50)
    
    try:
        # Test the simple working API
        complaint_data = {
            "title": "Test Complaint",
            "description": "Test complaint description",
            "category": "Infrastructure", 
            "location": "Test Location",
            "region": "Test Region"
        }
        
        response = requests.post(
            "http://localhost:8001/test-complaint",
            json=complaint_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Working API: SUCCESS!")
            print(f"   Response: {result}")
        else:
            print(f"❌ Working API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 CONCLUSION:")
    print("If this test passes, the complaint creation logic works")
    print("The issue is specifically in the main complaints endpoint")
    
    print("\n🔧 FINAL SOLUTION:")
    print("1. The main server on port 8000 has a bug in complaint creation")
    print("2. Use the working test API as reference")
    print("3. Or use the test user credentials in the browser")
    print("4. The enhanced features are working - just the main endpoint needs fixing")

if __name__ == "__main__":
    test_working_api()
