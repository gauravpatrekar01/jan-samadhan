import re
import os
import asyncio
import logging
import google.generativeai as genai
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    logger.warning("GEMINI_API_KEY not found in environment variables. AI summarization will be disabled.")
    model = None

# Cache for summaries (1000 items, 1 hour TTL)
summary_cache = TTLCache(maxsize=1000, ttl=3600)

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


def _detect_severity_hint(text: str) -> str:
    t = (text or "").lower()
    emergency_keywords = ["emergency", "urgent", "critical", "तातडी", "आपत्कालीन", "धोकादायक", "danger", "accident"]
    high_keywords = ["high", "important", "लवकर", "त्वरित", "गंभीर", "severe", "risk"]
    if any(k in t for k in emergency_keywords):
        return "अत्यंत उच्च"
    if any(k in t for k in high_keywords):
        return "उच्च"
    return "सामान्य"


def _ensure_two_to_three_lines(summary: str) -> str:
    lines = [line.strip() for line in (summary or "").splitlines() if line.strip()]
    if not lines:
        return "समस्या: माहिती उपलब्ध नाही\nतपशील: तक्रार प्रक्रिया करण्यात अडचण आली.\nतातडी: सामान्य"
    if len(lines) == 1:
        lines.append("तपशील: उपलब्ध नाही.")
        lines.append("तातडी: सामान्य")
    elif len(lines) == 2:
        lines.append("तातडी: सामान्य")
    elif len(lines) > 3:
        lines = lines[:3]
    return "\n".join(lines)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=False
)
async def _call_gemini(prompt: str) -> str | None:
    if not model:
        return None
    
    try:
        # Run in a thread to avoid blocking if the SDK is not fully async
        # (Though most modern SDKs handle this, safety first)
        response = await asyncio.to_thread(model.generate_content, prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise e
    return None


async def generate_summary(
    text: str,
    target_language: str = "Marathi",
    category: str | None = None
) -> str:
    """
    Generate a concise AI summary using Google Gemini API.
    Supports Marathi and Hindi.
    """
    cleaned_input = _clean_text(text)
    if not cleaned_input:
        return "समस्या: माहिती उपलब्ध नाही\nतपशील: तक्रारीची माहिती उपलब्ध नाही.\nतातडी: सामान्य"

    # Check cache
    cache_key = f"{hash(cleaned_input)}_{target_language}"
    if cache_key in summary_cache:
        return summary_cache[cache_key]

    prompt = f"""You are an AI assistant for a Smart Public Grievance and Resolution System used in Maharashtra, India.

This system uses the Google Gemini API for AI-powered translation and summarization.

Your task is to:
1. Analyze the citizen complaint.
2. Translate the complaint into the requested language.
3. Generate a concise government-style summary.

Supported Target Languages:
- Marathi
- Hindi

Instructions:
- The target language will be provided dynamically.
- Translate the complaint completely into the requested language.
- Generate exactly 3 short lines.
- Use simple, formal, citizen-friendly language.
- Clearly identify the main civic issue.
- Mention urgency if the complaint indicates:
  - danger
  - accidents
  - emergencies
  - severe infrastructure damage
  - health risks
  - electricity hazards
  - water shortage
- Preserve important complaint details accurately.
- Include location naturally if present in the complaint.
- Avoid unnecessary English words unless unavoidable.
- Do not hallucinate or invent details.
- Do not add explanations, markdown, bullet points, or extra text.
- Output must be clean and directly usable in a government dashboard UI.

Strict Output Format:

समस्या: <main issue>

तपशील: <translated concise complaint summary>

तातडी: <सामान्य / उच्च / अत्यंत उच्च>

Target Language:
{target_language}

Citizen Complaint:
{cleaned_input}
"""

    try:
        result = await _call_gemini(prompt)
        if result:
            # Clean up any potential markdown or extra whitespace
            final_summary = result.replace("```", "").strip()
            # Ensure it follows the 3-line rule
            final_summary = _ensure_two_to_three_lines(final_summary)
            summary_cache[cache_key] = final_summary
            return final_summary
    except Exception as e:
        logger.error(f"Failed to generate summary with Gemini: {e}")

    # Fallback logic
    severity = _detect_severity_hint(cleaned_input)
    fallback = (
        f"समस्या: {'माहिती उपलब्ध नाही' if target_language == 'Marathi' else 'जानकारी उपलब्ध नहीं'}\n"
        f"तपशील: {'तक्रार प्रक्रिया करण्यात अडचण आली.' if target_language == 'Marathi' else 'शिकायत संसाधित करने में समस्या आई।'}\n"
        f"तातडी: {severity if target_language == 'Marathi' else ('सामान्य' if severity == 'सामान्य' else ('उच्च' if severity == 'उच्च' else 'अत्यंत उच्च'))}"
    )
    return fallback


async def generate_marathi_summary(text: str) -> str:
    """
    Backward compatible Marathi summary generator.
    Redirects to the new Gemini-powered generate_summary.
    """
    return await generate_summary(text, target_language="Marathi")

