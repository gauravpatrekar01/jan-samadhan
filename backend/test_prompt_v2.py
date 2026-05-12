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
Your task is to take the following raw citizen complaint and convert it into a professional, concise 3-line summary in Marathi for an official government dashboard.

Target Language: Marathi (Strictly use ONLY this language script)
Category: Transport

Processing Rules:
1. Translate the entire meaning into Marathi. Do not leave English text in the summary.
2. Be specific: Identify the exact problem.
3. Tone: Formal and official.
4. Formatting: Exactly 3 lines with Marathi labels.

Strict 3-Line Output Template (in Marathi):
समस्या: [Core issue summary]
तपशील: [Brief detail about impact or location]
तातडी: [Urgency: सामान्य OR उच्च OR अत्यंत उच्च]

Citizen Complaint to Process:
{complaint}
"""
    
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-flash-latest",
            contents=prompt
        )
        with open("ai_raw_output.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Success: Output saved to ai_raw_output.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_prompt())
