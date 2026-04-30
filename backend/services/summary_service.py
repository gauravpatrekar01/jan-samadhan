import re


MARATHI_UNICODE_RE = re.compile(r"[\u0900-\u097F]")


def _clean_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def _is_marathi_text(text: str) -> bool:
    if not text:
        return False
    marathi_chars = len(MARATHI_UNICODE_RE.findall(text))
    return marathi_chars >= max(8, len(text) // 10)


def _truncate_sentence(text: str, max_chars: int = 180) -> str:
    cleaned = _clean_text(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"


def _detect_issue_type(text: str, category: str | None = None) -> str:
    t = (text or "").lower()
    if category:
        return category
    if any(k in t for k in ["water", "पाणी"]):
        return "पाणीपुरवठा"
    if any(k in t for k in ["electric", "वीज"]):
        return "वीज"
    if any(k in t for k in ["road", "pothole", "रस्ता", "खड्ड"]):
        return "रस्ते समस्या"
    if any(k in t for k in ["garbage", "waste", "कचरा", "स्वच्छ"]):
        return "स्वच्छता"
    return "नागरी समस्या"


def _detect_severity_hint(text: str) -> str:
    t = (text or "").lower()
    emergency_keywords = ["emergency", "urgent", "critical", "तातडी", "आपत्कालीन", "धोकादायक"]
    high_keywords = ["high", "important", "लवकर", "त्वरित", "गंभीर"]
    if any(k in t for k in emergency_keywords):
        return "तातडी: अत्यंत उच्च"
    if any(k in t for k in high_keywords):
        return "तातडी: उच्च"
    return "तातडी: सामान्य"


def _simple_marathi_translate(text: str) -> str:
    """
    Lightweight rule-based fallback translation.
    Keeps latency low and avoids external API dependencies.
    """
    dictionary = {
        "pothole": "खड्डा",
        "potholes": "खड्डे",
        "road": "रस्ता",
        "roads": "रस्ते",
        "water": "पाणी",
        "supply": "पुरवठा",
        "electricity": "वीज",
        "garbage": "कचरा",
        "drainage": "निचरा",
        "sewage": "सांडपाणी",
        "street light": "रस्त्यावरील दिवा",
        "urgent": "तातडीचे",
        "emergency": "आपत्कालीन",
        "complaint": "तक्रार",
        "problem": "समस्या",
        "issue": "अडचण",
        "location": "ठिकाण",
        "city": "शहर",
        "area": "परिसर",
    }
    translated = _clean_text(text)
    for en, mr in dictionary.items():
        translated = re.sub(rf"\b{re.escape(en)}\b", mr, translated, flags=re.IGNORECASE)
    return translated


def _ensure_two_to_three_lines(summary: str) -> str:
    lines = [line.strip() for line in (summary or "").splitlines() if line.strip()]
    if not lines:
        return "समस्या: माहिती उपलब्ध नाही.\nठिकाण: उपलब्ध नाही.\nतातडी: सामान्य"
    if len(lines) == 1:
        lines.append("ठिकाण: उपलब्ध नाही.")
        lines.append("तातडी: सामान्य")
    elif len(lines) == 2:
        lines.append("तातडी: सामान्य")
    elif len(lines) > 3:
        lines = lines[:3]
    return "\n".join(lines)


async def generate_marathi_summary(text: str) -> str:
    """
    Generate a short Marathi summary (2-3 lines) from complaint text.
    """
    cleaned = _clean_text(text)
    if not cleaned:
        return "तक्रारीची माहिती उपलब्ध नाही."

    if _is_marathi_text(cleaned):
        chunks = re.split(r"[.!?\n]+", cleaned)
        chunks = [_truncate_sentence(c, 140) for c in chunks if c.strip()]
        if not chunks:
            return _ensure_two_to_three_lines(_truncate_sentence(cleaned, 180))
        return _ensure_two_to_three_lines("\n".join(chunks[:3]))

    translated = _simple_marathi_translate(cleaned)
    issue = _detect_issue_type(cleaned)
    severity = _detect_severity_hint(cleaned)
    line1 = f"समस्या: {issue} संदर्भातील तक्रार नोंदवली आहे."
    line2 = f"तपशील: {_truncate_sentence(translated, 120)}"
    line3 = severity
    return _ensure_two_to_three_lines("\n".join([line1, line2, line3]))

