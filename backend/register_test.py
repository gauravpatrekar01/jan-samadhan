import requests
import json
from security import create_access_token
from datetime import timedelta

def test_register():
    # 1. Generate token
    token = create_access_token(
        data={"sub": "citizen@test.com", "role": "citizen"},
        expires_delta=timedelta(minutes=60)
    )
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # FormData fields for consistency
    form_data = {
        "title": "Water Leakage Issue",
        "description": "Massive water leakage in our locality since morning. Requesting urgent fix.",
        "category": "Water Supply",
        "priority": "medium",
        "location": "Shivaji Nagar",
        "region": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567
    }

    # 4. Try with media (multipart) - INVALID FILE TYPE
    print("\nSending POST request to /api/complaints/with-media (invalid file type) ...")
    files_invalid = {
        'files': ('test.txt', 'This is a test file content', 'text/plain')
    }
    
    response_media = requests.post(
        "http://localhost:8000/api/complaints/with-media",
        data=form_data,
        files=files_invalid,
        headers=headers
    )
    print(f"Status Code: {response_media.status_code}")
    print(f"Response: {response_media.text}")

    # 5. Try with empty files (multipart)
    print("\nSending POST request to /api/complaints/with-media (empty files) ...")
    
    response_empty_media = requests.post(
        "http://localhost:8000/api/complaints/with-media",
        data=form_data,
        headers=headers
    )
    
    print(f"Status Code: {response_empty_media.status_code}")
    print(f"Response: {response_empty_media.text}")

if __name__ == "__main__":
    test_register()
