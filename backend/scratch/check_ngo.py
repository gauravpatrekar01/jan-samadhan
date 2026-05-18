import sys
sys.path.insert(0, 'backend')
from db import db

def check_ngo():
    collection = db.get_collection("users")
    ngo_users = list(collection.find({"role": "ngo"}))
    print(f"Found {len(ngo_users)} NGO users:")
    for user in ngo_users:
        print("-" * 50)
        for k, v in user.items():
            if k == '_id':
                print(f"  _id: {str(v)}")
            elif k == 'password':
                print(f"  password: [HASHED] {v[:20]}...")
            else:
                print(f"  {k}: {v}")

if __name__ == '__main__':
    check_ngo()
