import os
import asyncio
from google import genai
from dotenv import load_dotenv

async def test_prompt():
    load_dotenv()
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY2"))
    
    complaint = "Bus समस्या. There are no government buses in Hingoli (central bus stand) This arises some issues for citizens due to no transport available in city."
    
    prompt = f"""
You are an expert Government Public Relations Officer in Maharashtra. 
Your task is to take the following raw citizen complaint and convert it into a professional, concise 3-line summary for an official government dashboard.

Target Language: Marathi (Strictly use ONLY this language)
Category: Transport

Processing Rules:
1. Detect the original language but TRANSLATE EVERYTHING into Marathi.
2. Be specific: Instead of saying "Complaint registered", summarize exactly WHAT the problem is (e.g., "हिंगोली बस स्थानकावर सरकारी बसेसचा अभाव").
3. Tone: Formal, official, and direct.
4. Formatting: Exactly 3 lines. No markdown. No bold. No bullets.

Strict 3-Line Output Template (in Marathi):
समस्या: [Specific core issue]
तपशील: [One concise sentence explaining impact/location]
तातडी: [Urgency level: सामान्य OR उच्च OR अत्यंत उच्च]

Citizen Complaint to Process:
{complaint}
"""
    
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-flash-latest",
            contents=prompt
        )
        print("--- AI RESPONSE ---")
        print(response.text)
        print("-------------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_prompt())
