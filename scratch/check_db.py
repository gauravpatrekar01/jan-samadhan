from db import db
import json

def check_extensions():
    col = db.get_collection("extension_requests")
    reqs = list(col.find({}))
    print(f"Total extension requests: {len(reqs)}")
    for r in reqs:
        print(json.dumps(str(r)))

if __name__ == "__main__":
    check_extensions()
