from db import db
import json

def list_projects():
    col = db.get_collection("projects")
    projects = list(col.find({}))
    for p in projects:
        print(f"ID: {p.get('project_id')}, Deadline: {p.get('current_deadline')}")

if __name__ == "__main__":
    list_projects()
