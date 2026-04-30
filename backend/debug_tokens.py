#!/usr/bin/env python3
"""
Debug Refresh Token Issue
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Test the decode function directly
try:
    from security import decode_token, create_refresh_token, create_access_token
    
    print("🔍 Testing Token Functions")
    print("=" * 40)
    
    # Create a test refresh token
    test_data = {"sub": "test@example.com", "role": "citizen"}
    refresh_token = create_refresh_token(test_data)
    print(f"✅ Created refresh token: {refresh_token[:20]}...")
    
    # Decode it
    decoded = decode_token(refresh_token)
    if decoded:
        print(f"✅ Decoded successfully: {decoded}")
    else:
        print("❌ Failed to decode refresh token")
    
    # Test access token creation
    access_token = create_access_token(test_data)
    print(f"✅ Created access token: {access_token[:20]}...")
    
    # Test decode access token
    decoded_access = decode_token(access_token)
    if decoded_access:
        print(f"✅ Decoded access token: {decoded_access}")
    else:
        print("❌ Failed to decode access token")
        
except Exception as e:
    print(f"❌ Error testing token functions: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 40)
