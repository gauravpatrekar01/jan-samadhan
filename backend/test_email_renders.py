import sys
import os
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import asyncio
from typing import Dict, Any

# Ensure backend directory is in path
sys.path.append(os.path.dirname(__file__))

from services.email_service import email_service

# Define test contexts for all 5 templates
TEST_CASES = {
    "complaint_submitted": {
        "citizen_name": "Shridhar Gurav",
        "complaint_id": "JSM-2026-5B039A9F",
        "category": "General",
        "priority": "High",
        "timestamp": "2026-05-18 13:11:21",
        "portal_url": "https://jansamadhan.gov.in/track/JSM-2026-5B039A9F"
    },
    "complaint_assigned": {
        "officer_name": "Deputy Commissioner Shinde",
        "complaint_id": "JSM-2026-5B039A9F",
        "category": "Water Supply",
        "priority": "High",
        "department": "Public Works Department",
        "deadline": "2026-05-20 13:11:21",
        "timestamp": "2026-05-18 14:15:00",
        "portal_url": "https://jansamadhan.gov.in/officer/dashboard"
    },
    "complaint_resolved": {
        "citizen_name": "Shridhar Gurav",
        "complaint_id": "JSM-2026-5B039A9F",
        "category": "General",
        "remarks": "The pipeline leakage has been successfully repaired and pressure testing completed. Normal supply is restored.",
        "timestamp": "2026-05-18 14:20:00",
        "portal_url": "https://jansamadhan.gov.in/rate/JSM-2026-5B039A9F"
    },
    "complaint_updated": {
        "citizen_name": "Shridhar Gurav",
        "complaint_id": "JSM-2026-5B039A9F",
        "new_status": "In Progress",
        "remarks": "Excavation team has reached the site and is beginning the repair work.",
        "timestamp": "2026-05-18 13:45:00",
        "portal_url": "https://jansamadhan.gov.in/track/JSM-2026-5B039A9F"
    },
    "sla_breach": {
        "admin_name": "Chief Administrator",
        "complaint_id": "JSM-2026-5B039A9F",
        "category": "Water Supply Leakage",
        "officer_name": "Officer Ramesh Patil",
        "deadline": "2026-05-17 13:11:21",
        "portal_url": "https://jansamadhan.gov.in/admin/escalations"
    }
}

async def run_audit():
    print("==================================================")
    print("   JanSamadhan Email Notification Audit & Test   ")
    print("==================================================")
    
    # 1. Check SMTP Config
    print("\n[1] Checking SMTP Configuration...")
    print(f"SMTP Host:      {email_service.smtp_host}")
    print(f"SMTP Port:      {email_service.smtp_port}")
    print(f"SMTP User:      {email_service.smtp_user}")
    print(f"SMTP From:      {email_service.smtp_from}")
    print(f"SMTP Configured: {email_service._is_configured()}")
    
    if not email_service._is_configured():
        print("❌ WARNING: SMTP credentials are not configured or missing!")
    else:
        print("✅ SMTP configuration found.")

    # 2. Check Template Rendering
    print("\n[2] Testing Template Rendering...")
    render_errors = 0
    for template_name, context in TEST_CASES.items():
        try:
            print(f"Rendering '{template_name}'... ", end="")
            html = email_service.render_template(template_name, context)
            if "Notification:" in html and "Data:" in html:
                # If rendering fails, render_template returns fallback text containing these words
                print("❌ FAILED (Returned fallback plain text!)")
                render_errors += 1
            else:
                # Check for critical styling items
                has_vml = "v:roundrect" in html or "v:rect" in html
                has_presentation = 'role="presentation"' in html
                has_word_wrap = "word-break:break-word" in html or "overflow-wrap:break-word" in html or "word-break:break-word" in html
                
                print("✅ SUCCESS")
                print(f"   -> File Size:       {len(html)} bytes")
                print(f"   -> Outlook VML:     {'✅ Yes' if has_vml else '❌ No'}")
                print(f"   -> Table Roles:     {'✅ Yes' if has_presentation else '❌ No'}")
                print(f"   -> Text wrapping:   {'✅ Yes' if has_word_wrap else '❌ No'}")
        except Exception as e:
            print(f"❌ CRITICAL EXCEPTION: {e}")
            render_errors += 1
            
    if render_errors == 0:
        print("\n🎉 ALL templates compiled and rendered successfully!")
    else:
        print(f"\n❌ Found {render_errors} template rendering issues.")

    # 3. Test sending real email (if user requested or credentials exist)
    test_recipient = os.getenv("TEST_RECIPIENT", email_service.smtp_user)
    if test_recipient and email_service._is_configured():
        print(f"\n[3] Sending single test email to '{test_recipient}'...")
        # Let's send a complaint resolved notification as the live test email
        subject = "JanSamadhan Live Validation: Complaint Resolved"
        res = await email_service.send_email(
            test_recipient,
            subject,
            "complaint_resolved",
            TEST_CASES["complaint_resolved"]
        )
        if res.get("success"):
            print("✅ Live SMTP delivery test successful!")
        else:
            print(f"❌ Live SMTP delivery test failed: {res.get('message')}")
    else:
        print("\n[3] Skipping live SMTP delivery test (No recipient or no configuration).")

if __name__ == "__main__":
    asyncio.run(run_audit())
