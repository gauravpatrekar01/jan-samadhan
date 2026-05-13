import sys
import os

# Add parent directory to path to import db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db
from pymongo import ASCENDING

def merge_audit_logs():
    print("Starting Audit Log Merger...")
    
    try:
        db.connect()
        database = db.db
        collections = database.list_collection_names()
        
        if "audit_log" not in collections:
            print("INFO: 'audit_log' collection not found. Nothing to merge.")
            return

        source_col = database["audit_log"]
        target_col = database["audit_logs"]
        
        total_found = source_col.count_documents({})
        print(f"Found {total_found} entries in 'audit_log'.")
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for doc in source_col.find():
            try:
                # Check for duplicates by _id
                if not target_col.find_one({"_id": doc["_id"]}):
                    target_col.insert_one(doc)
                    migrated += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"ERROR migrating doc {doc.get('_id')}: {e}")
                errors += 1
                
        print("\nMigration Summary:")
        print(f"   - Total Processed: {total_found}")
        print(f"   - Migrated:        {migrated}")
        print(f"   - Skipped (Dupes): {skipped}")
        print(f"   - Errors:          {errors}")
        
        # Index verification as requested
        print("\nVerifying Indexes...")
        target_col.create_index([("timestamp", ASCENDING)])
        target_col.create_index([("actor_email", ASCENDING)])
        target_col.create_index([("user_email", ASCENDING)])
        target_col.create_index([("action", ASCENDING)])
        target_col.create_index([("resource_id", ASCENDING)])
        target_col.create_index([("complaint_id", ASCENDING)])
        print("Indexes verified.")
        
        if migrated + skipped == total_found:
            print(f"\nSuccess! All documents are now in 'audit_logs'.")
            print("Warning: The old collection 'audit_log' has NOT been deleted.")
            print("Warning: Please verify the data in your dashboard, then manually rename it to 'audit_log_backup'.")
        else:
            print("\nWarning: Migration finished but counts don't match exactly. Check for errors above.")

    except Exception as e:
        print(f"Critical Failure: {e}")

if __name__ == "__main__":
    merge_audit_logs()
