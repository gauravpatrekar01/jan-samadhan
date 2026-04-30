import re
from functools import lru_cache
from db import db


FAQ = [
    {"intent": "file_complaint", "keywords": ["file", "register", "submit", "complaint"], "answer": "You can file a grievance from the Register page and track it on your dashboard."},
    {"intent": "track_status", "keywords": ["track", "status", "where", "id"], "answer": "Use your Grievance ID in the Track Status section to get real-time updates."},
    {"intent": "escalation", "keywords": ["escalate", "delay", "unresolved"], "answer": "Unresolved complaints are auto-escalated by SLA rules; you may also contact support."},
]


@lru_cache(maxsize=256)
def _intent_from_text(text: str) -> str:
    t = (text or "").lower()
    for f in FAQ:
        if any(k in t for k in f["keywords"]):
            return f["intent"]
    if re.search(r"JSM-\d{4}-[A-Z0-9]+", text or "", re.IGNORECASE):
        return "status_lookup"
    return "general"


def chatbot_reply(query: str) -> dict:
    intent = _intent_from_text(query)
    if intent == "status_lookup":
        grievance_id = re.search(r"(JSM-\d{4}-[A-Z0-9]+)", query or "", re.IGNORECASE)
        gid = grievance_id.group(1).upper() if grievance_id else None
        if not gid:
            return {"intent": intent, "answer": "Please share a valid Grievance ID (e.g., JSM-2026-AB12CD34)."}
        complaint = db.get_collection("complaints").find_one({"id": gid}, {"_id": 0, "status": 1, "priority": 1, "category": 1})
        if not complaint:
            return {"intent": intent, "answer": f"I could not find complaint {gid}. Please verify the ID."}
        return {
            "intent": intent,
            "answer": f"Status for {gid}: {complaint.get('status', 'submitted')}. Priority: {complaint.get('priority', 'medium')}. Category: {complaint.get('category', 'N/A')}.",
            "data": {"id": gid, **complaint},
        }

    if intent == "general":
        return {"intent": intent, "answer": "Please describe your grievance or share your Grievance ID for status lookup."}

    answer = next((f["answer"] for f in FAQ if f["intent"] == intent), "I can help with complaint filing and tracking.")
    return {"intent": intent, "answer": answer}

