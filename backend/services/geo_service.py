from collections import defaultdict
from typing import Any


SEVERITY_WEIGHT = {
    "emergency": 4.0,
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

CATEGORY_COLOR_MAP = {
    "Infrastructure": "#2563eb",
    "Water Supply": "#0891b2",
    "Electricity": "#ca8a04",
    "Sanitation": "#7c3aed",
    "Transport": "#059669",
    "Law & Order": "#dc2626",
    "Healthcare": "#db2777",
    "Other": "#64748b",
}


def normalize_geo_complaint(doc: dict[str, Any]) -> dict[str, Any] | None:
    lat = doc.get("latitude")
    lng = doc.get("longitude")
    if lat is None or lng is None:
        geo = doc.get("location_geo") or {}
        coords = geo.get("coordinates") or []
        if len(coords) == 2:
            lng, lat = coords[0], coords[1]
    if lat is None or lng is None:
        return None

    priority = (doc.get("priority") or "medium").lower()
    category = doc.get("category") or "Other"
    return {
        "id": doc.get("id"),
        "title": doc.get("title"),
        "category": category,
        "priority": priority,
        "status": (doc.get("status") or "submitted").lower(),
        "region": doc.get("region") or "Unknown",
        "latitude": float(lat),
        "longitude": float(lng),
        "severity_score": SEVERITY_WEIGHT.get(priority, 2.0),
        "marker_color": CATEGORY_COLOR_MAP.get(category, "#64748b"),
        "createdAt": doc.get("createdAt") or doc.get("timestamp"),
    }


def cluster_geo_points(points: list[dict[str, Any]], precision: int = 2) -> list[dict[str, Any]]:
    buckets: dict[tuple[float, float], dict[str, Any]] = {}
    for p in points:
        key = (round(p["latitude"], precision), round(p["longitude"], precision))
        if key not in buckets:
            buckets[key] = {
                "cell_latitude": key[0],
                "cell_longitude": key[1],
                "count": 0,
                "emergency_count": 0,
                "high_count": 0,
                "categories": defaultdict(int),
                "risk_score": 0.0,
            }
        entry = buckets[key]
        entry["count"] += 1
        entry["categories"][p["category"]] += 1
        if p["priority"] == "emergency":
            entry["emergency_count"] += 1
        if p["priority"] == "high":
            entry["high_count"] += 1
        entry["risk_score"] += p["severity_score"]

    clusters = []
    for c in buckets.values():
        categories = dict(c["categories"])
        avg_risk = c["risk_score"] / max(c["count"], 1)
        c["risk_score"] = round(avg_risk * 25, 2)
        c["dominant_category"] = max(categories, key=categories.get) if categories else "Other"
        c["categories"] = categories
        clusters.append(c)
    clusters.sort(key=lambda x: x["risk_score"], reverse=True)
    return clusters


def detect_high_risk_zones(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in clusters if c["risk_score"] >= 60 or c["emergency_count"] >= 2]

