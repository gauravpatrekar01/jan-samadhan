"""
One-time migration: sanitize votes_history keys.
MongoDB field keys cannot contain dots, so email-based keys like
"user@example.com" must be converted to "user@example_dot_com".
This script also removes any duplicate vote entries.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME", "jansamadhan")]


def migrate():
    collection = db.get_collection("complaints")
    complaints = list(collection.find(
        {"votes_history": {"$exists": True, "$ne": {}}},
        {"_id": 0, "id": 1, "votes_history": 1, "votes": 1}
    ))

    print(f"Found {len(complaints)} complaints with vote history")
    migrated = 0

    for c in complaints:
        history = c.get("votes_history", {})
        new_history = {}
        needs_migration = False

        for key, value in history.items():
            safe_key = key.replace(".", "_dot_")
            if safe_key != key:
                needs_migration = True
            # Keep latest vote per user (dedup)
            new_history[safe_key] = value

        if needs_migration:
            # Recalculate vote count from clean history
            up_count = sum(1 for v in new_history.values() if v == "up")
            down_count = sum(1 for v in new_history.values() if v == "down")
            correct_votes = up_count - down_count

            collection.update_one(
                {"id": c["id"]},
                {"$set": {
                    "votes_history": new_history,
                    "votes": correct_votes
                }}
            )
            migrated += 1
            print(f"Migrated {c['id']}: {len(history)} -> {len(new_history)} entries, votes={correct_votes}")

    print(f"\nMigration complete. {migrated} complaints updated.")


if __name__ == "__main__":
    migrate()
