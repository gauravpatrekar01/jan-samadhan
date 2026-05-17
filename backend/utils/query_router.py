import re
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class QueryRouter:
    def __init__(self):
        # Patterns for KPI requests
        self.kpi_patterns = [
            r'total.*complaint', r'pending.*complaint', r'resolved.*complaint',
            r'how many complaint', r'dashboard.*kpi', r'sla.*violation',
            r'average.*time', r'in progress.*complaint', r'rejected.*complaint',
            r'analytics', r'officer dashboard'
        ]
        
        # Patterns for static help
        self.login_patterns = [r'login', r'sign in', r'password', r'cannot access']
        self.track_patterns = [r'track.*complaint', r'complaint status', r'where is my complaint']

    def route_query(self, query: str) -> Tuple[bool, str, str]:
        """
        Routes query to determine if it should be handled locally or via Gemini.
        Returns: (is_local, action_type, static_response_if_any)
        """
        query_lower = query.lower()
        
        # Check KPI patterns
        for pattern in self.kpi_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"Query routed locally: KPI request matched pattern '{pattern}'")
                return True, "kpi", ""
                
        # Check static login help
        for pattern in self.login_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"Query routed locally: Login help")
                return True, "static", "JanSamadhan: Login requires a valid citizen, officer, NGO, or admin account. If your login isn't working, verify the email/password or make sure the database is running. Officers and NGOs must be approved by an Admin."
                
        # Check static track help
        for pattern in self.track_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"Query routed locally: Tracking help")
                return True, "static", "JanSamadhan: You can track your complaint status in the Citizen Dashboard or the Public Grievance section using the complaint ID."

        # Otherwise route to AI
        logger.info("Query routed to AI")
        return False, "ai", ""

query_router = QueryRouter()
