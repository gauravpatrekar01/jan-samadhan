from datetime import datetime, timedelta, timezone


def _parse_iso(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def moving_average_forecast(series: list[int], window: int = 3, steps: int = 3) -> list[float]:
    if not series:
        return [0.0] * steps
    values = list(series)
    result = []
    for _ in range(steps):
        frame = values[-window:] if len(values) >= window else values
        avg = round(sum(frame) / max(len(frame), 1), 2)
        result.append(avg)
        values.append(avg)
    return result


def build_daily_trend(docs: list[dict], days: int = 30) -> list[dict]:
    now = datetime.now(timezone.utc).date()
    buckets = {(now - timedelta(days=i)).isoformat(): {"total": 0, "resolved": 0} for i in range(days - 1, -1, -1)}
    for d in docs:
        dt = _parse_iso(d.get("createdAt") or d.get("created_at") or d.get("timestamp"))
        if not dt:
            continue
        key = dt.date().isoformat()
        if key not in buckets:
            continue
        buckets[key]["total"] += 1
        if (d.get("status") or "").lower() in {"resolved", "closed"}:
            buckets[key]["resolved"] += 1
    return [{"date": k, **v} for k, v in buckets.items()]

