import os
import asyncio
import logging
from google import genai
from google.genai import types

from cachetools import TTLCache
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import settings

logger = logging.getLogger(__name__)

from services.gemini_pool import gemini_pool

# Cache
summary_cache = TTLCache(maxsize=1000, ttl=3600)

def _clean_text(text: str) -> str:
    return " ".join((text or "").strip().split())

def _sanitize_output(text: str) -> str:
    """
    Remove markdown and normalize output to exactly 3 lines with Marathi labels.
    """
    if not text:
        return ""
        
    cleaned = (
        text.replace("```", "")
        .replace("`", "")
        .replace("*", "")
        .replace("#", "")
        .strip()
    )

    lines = [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip()
    ]
    
    # Priority for lines containing the actual labels
    result_lines = []
    for line in lines:
        if any(label in line for label in ["समस्या:", "तपशील:", "तातडी:"]):
            result_lines.append(line)
        if len(result_lines) == 3:
            break
            
    if len(result_lines) == 3:
        return "\n".join(result_lines)

    # Fallback to taking first 3 lines and ensuring they are labeled
    if len(lines) > 3:
        lines = lines[:3]
    
    while len(lines) < 3:
        if len(lines) == 0:
            lines.append("समस्या: माहिती उपलब्ध नाही")
        elif len(lines) == 1:
            lines.append("तपशील: तपशील उपलब्ध नाही")
        else:
            lines.append("तातडी: सामान्य")
            
    # Ensure lines have labels if AI forgot them
    if not lines[0].startswith("समस्या:"): lines[0] = f"समस्या: {lines[0]}"
    if not lines[1].startswith("तपशील:"): lines[1] = f"तपशील: {lines[1]}"
    if not lines[2].startswith("तातडी:"): lines[2] = f"तातडी: {lines[2]}"
            
    return "\n".join(lines)



async def generate_summary(
    text: str,
    target_language: str = "Marathi",
    category: str | None = None,
) -> str:
    """
    AI-powered multilingual complaint translator and summarizer with key failover.
    """
    cleaned_input = _clean_text(text)
    logger.info(f"Generating {target_language} summary (len={len(cleaned_input)})")

    if not cleaned_input:
        return _sanitize_output("")

    cache_key = f"{hash(cleaned_input)}_{target_language}"
    if cache_key in summary_cache:
        return summary_cache[cache_key]

    prompt = f"""
You are an expert Government Public Relations Officer in Maharashtra. 
Your task is to take the following raw citizen complaint and convert it into a professional, concise 3-line summary in {target_language} for an official government dashboard.

Target Language: {target_language} (Strictly use ONLY this language script)
Category: {category or "General Civic Issue"}

Processing Rules:
1. Translate the entire meaning into {target_language}. Do not leave English text in the summary.
2. Be specific: Identify the exact problem (e.g., location, landmark, specific issue).
3. Tone: Formal and official.
4. Formatting: Exactly 3 lines with the following labels in {target_language}:

समस्या: [Core issue summary]
तपशील: [Brief detail about impact or location]
तातडी: [Urgency: सामान्य OR उच्च OR अत्यंत उच्च]

Citizen Complaint to Process:
{cleaned_input}
"""

    try:
        ai_result = await gemini_pool.generate_content_async(
            prompt=prompt,
            system_instruction="You are an expert Government Public Relations Officer in Maharashtra.",
            model="gemini-2.5-flash"
        )
        if ai_result and ai_result["response"]:
            final_summary = _sanitize_output(ai_result["response"])
            summary_cache[cache_key] = final_summary
            logger.info("Summary generated successfully.")
            return final_summary
    except Exception as e:
        last_error = e
        logger.error(f"Gemini pool failover failed. Fallback triggered. Last error: {last_error}")

    # Fallback
    severity = "सामान्य"
    if any(k in cleaned_input.lower() for k in ["emergency", "urgent", "critical", "तातडी", "धोका"]):
        severity = "अत्यंत उच्च"
    elif any(k in cleaned_input.lower() for k in ["high", "risk", "लवकर"]):
        severity = "उच्च"

    if target_language.lower() == "hindi":
        return (
            f"समस्या: शिकायत संसाधित नहीं हो सकी\n"
            f"तपशील: सेवा अभी व्यस्त है, कृपया बाद में पुनः प्रयास करें।\n"
            f"तातडी: {severity}"
        )

    return (
        f"समस्या: तक्रार प्रक्रिया पूर्ण होऊ शकली नाही\n"
        f"तपशील: सेवा सध्या व्यस्त आहे, कृपया पुन्हा प्रयत्न करा.\n"
        f"तातडी: {severity}"
    )

async def generate_marathi_summary(text: str) -> str:
    return await generate_summary(text=text, target_language="Marathi")
