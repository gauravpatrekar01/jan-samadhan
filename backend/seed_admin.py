import os
from db import db
from security import hash_password
from datetime import datetime, timezone

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
ADMIN_NAME = os.getenv('ADMIN_NAME', 'Administrator')

if not ADMIN_EMAIL or not ADMIN_PASSWORD:
    print('Please set ADMIN_EMAIL and ADMIN_PASSWORD environment variables.')
    print('Example: ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=S3cur3P@ss python seed_admin.py')
    exit(1)

collection = db.get_collection('users')
existing = collection.find_one({'email': ADMIN_EMAIL})
if existing:
    print(f'Admin user already exists: {ADMIN_EMAIL}')
    exit(0)

user = {
    'name': ADMIN_NAME,
    'email': ADMIN_EMAIL,
    'password': hash_password(ADMIN_PASSWORD),
    'role': 'admin',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'verified': True,
}

collection.insert_one(user)
print(f'Admin user created: {ADMIN_EMAIL}')
