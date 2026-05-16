from db import db
import json

def check_project():
    col = db.get_collection("projects")
    p = col.find_one({"project_id": "PROJ-3049E60E"})
    if p:
        print(f"Project found: {p['title']}")
    else:
        print("Project NOT found in database")

if __name__ == "__main__":
    check_project()
