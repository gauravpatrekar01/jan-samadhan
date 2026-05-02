from db import db
count = db.get_collection("complaints").count_documents({})
print(f"Complaints count: {count}")

# Print a sample complaint to see structure
sample = db.get_collection("complaints").find_one({}, {"_id": 0})
print(f"Sample: {sample}")

# Print users count
user_count = db.get_collection("users").count_documents({})
print(f"Users count: {user_count}")
