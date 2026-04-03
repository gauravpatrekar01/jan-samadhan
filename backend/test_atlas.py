from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')

print(f"Testing URI: {uri.replace('admin%24rise_10Gp', '***')}")
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    print("STATUS:", client.admin.command('ping'))
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
