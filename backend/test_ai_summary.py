import asyncio
import sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.append(os.path.dirname(__file__))

from services.summary_service import generate_summary

async def main():
    test_complaint = (
        "There is a huge pipeline leakage near the main gate of Shivaji Park in Dadar. "
        "Drinking water is being wasted in large quantities and the road is completely flooded. "
        "Please fix this immediately."
    )
    print("Testing generate_summary...")
    try:
        summary = await generate_summary(test_complaint, target_language="Marathi")
        print("\n=== AI SUMMARY RESULT ===")
        print(summary)
        print("=========================")
        if "सेवा सध्या व्यस्त आहे" in summary:
            print("⚠️ WARNING: Fallback triggered (Gemini model failed or API keys expired/rate-limited).")
        else:
            print("✅ SUCCESS: AI summary is fully functional!")
    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
