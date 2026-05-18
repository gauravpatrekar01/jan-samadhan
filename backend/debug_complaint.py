import sys
sys.path.insert(0, '.')
from db import db

c = db.get_collection('complaints')

# Check all complaints
print("=== ALL COMPLAINTS ===")
for doc in c.find({}, {'id':1,'status':1,'is_deleted':1}):
    print(f"  id={doc.get('id')} status={doc.get('status')} is_deleted={doc.get('is_deleted')}")

print()
# Check specific doc
doc = c.find_one({'id': 'JSM-2026-TEST123'})
if doc:
    print("Found by id:", doc.get('id'))
    print("is_deleted:", doc.get('is_deleted'))
else:
    print("NOT FOUND by {'id': 'JSM-2026-TEST123'}")

# Try the filtered query that GET endpoint uses
doc2 = c.find_one({'id': 'JSM-2026-TEST123', 'is_deleted': {'$ne': True}})
print("Filtered find_one:", doc2.get('id') if doc2 else "FILTERED OUT - is_deleted=True!")

# Also check if there's an 'is_deleted: True' blocking
doc3 = c.find_one({'is_deleted': True})
print("Any deleted docs?", doc3.get('id') if doc3 else "No deleted docs in DB")
