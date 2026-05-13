from db import db
import json

def debug_complaints():
    collection = db.get_collection("complaints")
    complaints = list(collection.find().sort("createdAt", -1).limit(5))
    
    for c in complaints:
        print(f"Complaint ID: {c.get('id')}")
        print(f"  citizen_email: {c.get('citizen_email')} (type: {type(c.get('citizen_email'))})")
        print(f"  email: {c.get('email')} (type: {type(c.get('email'))})")
        print("-" * 30)

if __name__ == "__main__":
    debug_complaints()
