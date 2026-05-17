import logging
import asyncio
from typing import Dict, Any
from db import db
from services.cache_service import kpi_cache

logger = logging.getLogger(__name__)

class KPIService:
    def __init__(self):
        # We assume db is already initialized and connected
        self.collection = db.get_collection("complaints")

    async def get_kpi_stats(self) -> Dict[str, Any]:
        """Fetch and cache KPI stats asynchronously"""
        cache_key = "global_chatbot_kpis"
        cached_data = kpi_cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        logger.info("Executing DB query for chatbot KPIs")
        loop = asyncio.get_event_loop()
        
        # Run synchronous DB queries in an executor to avoid blocking the event loop
        def fetch_stats():
            total = self.collection.count_documents({})
            pending = self.collection.count_documents({"status": "submitted"})
            in_progress = self.collection.count_documents({"status": {"$in": ["under_review", "in_progress"]}})
            resolved = self.collection.count_documents({"status": {"$in": ["resolved", "closed"]}})
            rejected = self.collection.count_documents({"status": "rejected"})
            
            # Avg resolution time
            pipeline = [
                {"$match": {"status": {"$in": ["resolved", "closed"]}, "resolution_time_hours": {"$exists": True}}},
                {"$group": {"_id": None, "avg_time": {"$avg": "$resolution_time_hours"}}}
            ]
            res_stats = list(self.collection.aggregate(pipeline))
            avg_res_time = round(res_stats[0]["avg_time"], 1) if res_stats else 0
            
            # SLA violations
            sla_violations = self.collection.count_documents({"status": {"$in": ["resolved", "closed"]}, "sla_met": False})
            
            return {
                "total_complaints": total,
                "pending_complaints": pending,
                "in_progress_complaints": in_progress,
                "resolved_complaints": resolved,
                "rejected_complaints": rejected,
                "sla_violations": sla_violations,
                "avg_resolution_time_hours": avg_res_time
            }
            
        start_time = asyncio.get_event_loop().time()
        stats = await loop.run_in_executor(None, fetch_stats)
        query_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
        logger.info(f"DB Query Time: {query_time_ms} ms")
        
        kpi_cache.set(cache_key, stats)
        
        return stats

kpi_service = KPIService()
