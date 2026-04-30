from datetime import datetime, timezone, timedelta


KEYWORD_BOOST = {
    "fire": 3,
    "accident": 3,
    "flood": 3,
    "danger": 3,
    "emergency": 4,
    "urgent": 2,
    "hospital": 2,
    "water": 1,
    "electricity": 1,
}

SLA_HOURS = {
    "emergency": 24,
    "high": 48,
    "medium": 72,
    "low": 120,
}


def compute_priority_score(complaint: dict) -> int:
    text = f"{complaint.get('title', '')} {complaint.get('description', '')}".lower()
    base = {"low": 10, "medium": 20, "high": 30, "emergency": 40}.get((complaint.get("priority") or "medium").lower(), 20)
    keyword = sum(v for k, v in KEYWORD_BOOST.items() if k in text)
    votes = int(complaint.get("votes", 0))

    created = complaint.get("createdAt")
    age_bonus = 0
    if created:
        try:
            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            age_hours = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600)
            age_bonus = min(int(age_hours // 24), 10)
        except Exception:
            age_bonus = 0
    return base + keyword + min(votes, 15) + age_bonus


def next_sla_deadline(priority: str, start: datetime | None = None) -> str:
    now = start or datetime.now(timezone.utc)
    hours = SLA_HOURS.get((priority or "medium").lower(), 72)
    return (now + timedelta(hours=hours)).isoformat()


def escalate_complaint_doc(complaint: dict) -> dict:
    level = int(complaint.get("escalation_level", 0)) + 1
    new_priority = complaint.get("priority", "medium")
    if level >= 3:
        new_priority = "emergency"
    elif level == 2 and new_priority in {"low", "medium"}:
        new_priority = "high"

    return {
        "escalation_level": level,
        "priority": new_priority,
        "sla_deadline": next_sla_deadline(new_priority),
    }

