import sys
sys.path.insert(0, '.')
from db import db

print("--- ALL USER ROLES ---")
users = db.get_collection("users").find()
for u in users:
    print(f"Name: {u.get('name')}, Email: {u.get('email')}, Role: {u.get('role')}, Verified: {u.get('verified')}, Active: {u.get('is_active')}, Categories: {u.get('categories')}")

print("\n--- COMPLAINTS ---")
complaints = db.get_collection("complaints").find()
for c in complaints:
    print(f"ID: {c.get('id')}, Title: {c.get('title')}, Category: {c.get('category')}, Assigned NGO: {c.get('assigned_to_ngo')}")
