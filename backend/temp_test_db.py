from db import db
try:
    count = db.get_collection('complaints').count_documents({})
    print(f"Count: {count}")
except Exception as e:
    print(f"Error: {e}")
