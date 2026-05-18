import json
import logging
from datetime import datetime, timezone
from db import db
from services.gemini_pool import gemini_pool
from audit import log_audit
from errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)

class AIReportService:
    def __init__(self):
        pass

    def get_fallback_report(self, complaint: dict) -> dict:
        """
        Extremely robust rules-based fallback logic that matches the AI Report specification perfectly.
        Runs when Gemini is offline, rate-limited, or returns malformed response.
        """
        title = complaint.get("title", "")
        description = complaint.get("description", "")
        category = complaint.get("category", "")
        subcategory = complaint.get("subcategory", "")
        location = complaint.get("location", "")
        region = complaint.get("region", "")
        priority = complaint.get("priority", "medium")
        history = complaint.get("history", [])
        reopen_count = complaint.get("reopen_count", 0)
        
        # Determine votes count safely
        votes = complaint.get("upvotes", 0)
        if not votes and isinstance(complaint.get("votes"), list):
            votes = len(complaint.get("votes"))

        text = f"{title} {description} {category} {subcategory} {location} {region}".lower()
        
        # 1. Severity Score Computation (0-100)
        severity_score = 20  # Baseline
        
        # High impact triggers
        if any(k in text for k in ["billing irregularity", "billing", "fraud", "corruption", "bribe", "fund", "money", "audit"]):
            severity_score += 30
        if any(k in text for k in ["healthcare", "hospital", "doctor", "medical", "clinic", "health"]):
            severity_score += 25
        if any(k in text for k in ["government service failure", "failure", "delay", "negligence", "broken"]):
            severity_score += 20
        if reopen_count > 0 or len(history) > 2:
            severity_score += 15
        if votes > 5:
            severity_score += 10
            
        severity_score = min(100, severity_score)
        
        # Map Severity to Urgency Level
        if severity_score <= 30:
            urgency_level = "low"
        elif severity_score <= 60:
            urgency_level = "medium"
        elif severity_score <= 85:
            urgency_level = "high"
        else:
            urgency_level = "critical"
            
        # 2. Risk Analysis Flags
        fraud_risk = "low"
        if any(k in text for k in ["billing", "fraud", "corruption", "irregularity", "bribe", "fund"]):
            fraud_risk = "high"
        elif any(k in text for k in ["audit", "mismanagement", "money"]):
            fraud_risk = "medium"
            
        mismanagement_risk = "low"
        if any(k in text for k in ["mismanagement", "negligence", "delay", "failure", "broken"]):
            mismanagement_risk = "high"
        elif any(k in text for k in ["officer", "staff", "system"]):
            mismanagement_risk = "medium"
            
        escalation_risk = "low"
        if priority.lower() == "emergency" or reopen_count > 0:
            escalation_risk = "high"
        elif priority.lower() == "high" or len(history) > 1:
            escalation_risk = "medium"
            
        # 3. Category Validation
        ai_predicted_category = category
        if any(k in text for k in ["healthcare", "hospital", "doctor", "medical"]):
            ai_predicted_category = "Healthcare Finance Compliance" if "billing" in text or "fraud" in text else "Healthcare Services"
        elif any(k in text for k in ["infrastructure", "road", "drainage", "bridge"]):
            ai_predicted_category = "Civic Infrastructure"
        elif any(k in text for k in ["water", "leakage", "pipeline"]):
            ai_predicted_category = "Water Supply Management"
        elif any(k in text for k in ["electricity", "power", "meter"]):
            ai_predicted_category = "Electricity Utility"
            
        confidence = 0.95 if ai_predicted_category == category else 0.85
        
        # 4. Sentiment Analysis
        sentiment = "negative"
        if any(k in text for k in ["terrible", "worst", "unacceptable", "corruption", "fraud", "emergency", "urgent"]):
            sentiment = "highly_negative"
        elif priority.lower() in ["emergency", "high"]:
            sentiment = "highly_negative"
            
        # 5. Entity Extraction
        extracted_location = f"{location}, {region}" if location and region else (location or region or "Unknown")
        
        keywords = []
        for kw in ["billing irregularity", "financial mismanagement", "delay", "corruption", "water supply", "road repair", "electricity failure", "medical negligence"]:
            if kw in text:
                keywords.append(kw)
        if not keywords:
            keywords = [w for w in ["delay", "billing", "failure", "broken", "health", "water"] if w in text]
        if not keywords:
            keywords = ["complaint"]
            
        organizations = []
        if "hospital" in text or "clinic" in text:
            organizations.append("Government Hospital")
        if "municipal" in text or "corporation" in text:
            organizations.append("Municipal Corporation")
        if "msedcl" in text or "electricity board" in text:
            organizations.append("Electricity Distribution Board")
        if not organizations:
            organizations.append("Local Civic Authority")
            
        # 6. Department Recommendation
        recommended_department = "General Administration"
        if "healthcare" in text or "hospital" in text or "medical" in text:
            recommended_department = "Health Department"
            if "billing" in text or "fraud" in text:
                recommended_department = "Health + Finance Audit Cell"
        elif "billing" in text or "fraud" in text or "corruption" in text:
            recommended_department = "Audit / Finance Department"
        elif any(k in text for k in ["road", "drainage", "infrastructure", "bridge"]):
            recommended_department = "Municipal / PWD Department"
        elif any(k in text for k in ["water", "supply", "leakage"]):
            recommended_department = "Water Supply Department"
        elif any(k in text for k in ["police", "crime", "safety", "law"]):
            recommended_department = "Law Enforcement"
            
        # 7. Suggested Actions
        suggested_actions = []
        if recommended_department == "Health + Finance Audit Cell":
            suggested_actions = ["Initiate billing audit", "Assign senior compliance officer", "Investigate hospital financial records"]
        elif "Health" in recommended_department:
            suggested_actions = ["Conduct on-site inspection of medical facility", "Review doctor/staff assignment logs", "Contact patient/citizen for statement"]
        elif "Audit" in recommended_department or "Finance" in recommended_department:
            suggested_actions = ["Review transaction logs", "Audit department accounting files", "Request audit report from supervisor"]
        elif "Municipal" in recommended_department:
            suggested_actions = ["Dispatch field engineer for inspection", "Validate work order status", "Assess public safety impact"]
        elif "Water" in recommended_department:
            suggested_actions = ["Deploy pipeline repair team", "Perform quality check on water source", "Notify citizens of service restoration"]
        else:
            suggested_actions = ["Assign review officer to verify claims", "Contact citizen for clarification", "File report to Department Head"]
            
        # 8. Summary Insight
        summary_insight = f"The complaint highlights an issue regarding {category.lower()} in {extracted_location} with a {priority.lower()} priority."
        if "billing" in text or "fraud" in text:
            summary_insight = f"The complaint highlights possible financial mismanagement and irregular billing practices in {organizations[0]} affecting public trust."
        elif "health" in text or "medical" in text:
            summary_insight = f"The complaint points to critical medical or healthcare issues in {organizations[0]} needing prompt operational intervention."
        elif "water" in text or "supply" in text:
            summary_insight = f"A water supply disruption or infrastructure leak has been reported, impacting daily public life and safety."
            
        return {
            "summary_insight": summary_insight,
            "severity_score": severity_score,
            "urgency_level": urgency_level,
            "risk_flags": {
                "fraud_risk": fraud_risk,
                "mismanagement_risk": mismanagement_risk,
                "escalation_risk": escalation_risk
            },
            "category_validation": {
                "user_category": category,
                "ai_predicted_category": ai_predicted_category,
                "confidence": confidence
            },
            "sentiment": sentiment,
            "recommended_department": recommended_department,
            "suggested_actions": suggested_actions,
            "entity_extraction": {
                "location": extracted_location,
                "keywords": keywords,
                "organizations": organizations
            }
        }

    async def generate_ai_report(self, id: str, refresh: bool = False, performed_by: str = "system") -> dict:
        """
        AI intelligence report generation service.
        Fetches or computes a structured analysis of a complaint document.
        Does not mutate the workflow state or status of the complaint.
        """
        complaint_coll = db.get_collection("complaints")
        complaint = complaint_coll.find_one({"id": id})
        if not complaint:
            raise NotFoundError("Complaint")

        # 1. Cache Check: return cached report if it exists and refresh is not requested
        if not refresh and "ai_report" in complaint and complaint["ai_report"]:
            logger.info(f"Returning cached AI report for complaint {id}")
            report = complaint["ai_report"]
            report["complaint_id"] = id
            return report

        logger.info(f"Generating new AI Report for complaint {id}")

        # Gather inputs safely
        title = complaint.get("title", "")
        description = complaint.get("description", "")
        category = complaint.get("category", "")
        subcategory = complaint.get("subcategory", "")
        location = complaint.get("location", "")
        region = complaint.get("region", "")
        priority = complaint.get("priority", "medium")
        
        # Process history into a timeline text
        history_list = complaint.get("history", [])
        timeline_notes = "; ".join([f"{h.get('status', 'unknown')}: {h.get('remarks', 'no remarks')}" for h in history_list])

        # Step 1: Text Merge
        combined_text = f"Title: {title}\nDescription: {description}\nCategory: {category}\nSubcategory: {subcategory}\nLocation: {location}\nRegion: {region}\nPriority: {priority}\nTimeline notes: {timeline_notes}"

        # Construct Gemini Prompt
        prompt = f"""
You are an advanced AI Report Analyst for the JanSamadhan Grievance System.
Analyze the following complaint document and generate a structured intelligence report in strict JSON format.

Complaint Data:
{combined_text}

Your response must be a single valid JSON object containing exactly these keys and value types:
{{
  "summary_insight": "2-3 line structured summary focusing on issue + impact + urgency",
  "severity_score": int (0-100 computed based on triggers: financial mismanagement +30, healthcare risk +25, government service failure +20, repeated complaints +15, high votes +10),
  "urgency_level": "low" | "medium" | "high" | "critical",
  "risk_flags": {{
    "fraud_risk": "low" | "medium" | "high",
    "mismanagement_risk": "low" | "medium" | "high",
    "escalation_risk": "low" | "medium" | "high"
  }},
  "category_validation": {{
    "user_category": "{category}",
    "ai_predicted_category": "string (AI predicted category)",
    "confidence": float (between 0.0 and 1.0)
  }},
  "sentiment": "neutral" | "negative" | "highly_negative",
  "recommended_department": "string (best matching department like 'Health Department', 'Audit / Finance + Health', 'Municipal', 'Law Enforcement')",
  "suggested_actions": ["action 1", "action 2", "action 3"],
  "entity_extraction": {{
    "location": "string (normalized location)",
    "keywords": ["list", "of", "extracted", "keywords"],
    "organizations": ["list", "of", "extracted", "organizations"]
  }}
}}

Ensure no markdown formatting or backticks outside the JSON. Return only the raw JSON string.
"""

        report_data = None
        
        # 2. Try Gemini Pool Async
        try:
            ai_result = await gemini_pool.generate_content_async(
                prompt=prompt,
                system_instruction="You are an expert AI Report Analyst. Always output strictly valid JSON.",
                model="gemini-2.5-flash"
            )
            if ai_result and ai_result.get("response"):
                raw_response = ai_result["response"].strip()
                # Clean code blocks if present
                if raw_response.startswith("```"):
                    raw_response = raw_response.replace("```json", "", 1).replace("```", "", 1).strip()
                
                parsed = json.loads(raw_response)
                
                # Basic validation
                required_keys = ["summary_insight", "severity_score", "urgency_level", "risk_flags", "category_validation", "sentiment", "recommended_department", "suggested_actions", "entity_extraction"]
                if all(k in parsed for k in required_keys):
                    report_data = parsed
                    logger.info("Successfully generated AI report via Gemini pool.")
        except Exception as e:
            logger.error(f"Gemini AI Report generation encountered an issue, falling back to rule-based: {e}")

        # 3. Rules Fallback if LLM fails
        if not report_data:
            logger.info("Applying rules-based fallback for AI Report generation.")
            report_data = self.get_fallback_report(complaint)

        # Append generated metadata safely
        now_str = datetime.now(timezone.utc).isoformat()
        report_data["generated_at"] = now_str
        report_data["version"] = "v1"

        # 4. Storage (Option A recommended - embedded field)
        complaint_coll.update_one(
            {"id": id},
            {"$set": {"ai_report": report_data}}
        )

        # 5. Audit Logging (Mandatory)
        try:
            log_audit(
                action="AI_REPORT_GENERATED",
                actor_email=performed_by,
                actor_role="system" if performed_by == "system" else "user",
                resource_type="complaint",
                resource_id=id,
                details={
                    "complaint_id": id,
                    "severity_score": report_data.get("severity_score", 0),
                    "version": "v1"
                }
            )
        except Exception as audit_err:
            logger.error(f"Failed to log audit entry for AI Report: {audit_err}")

        # Return structured output with complaint_id at top level
        response_report = dict(report_data)
        response_report["complaint_id"] = id
        return response_report

ai_report_service = AIReportService()
