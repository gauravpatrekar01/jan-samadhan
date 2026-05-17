import time
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, ttl_seconds: int = 60):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                logger.info(f"Cache HIT for key: {key}")
                return entry["data"]
            else:
                logger.info(f"Cache EXPIRED for key: {key}")
                del self.cache[key]
        else:
            logger.info(f"Cache MISS for key: {key}")
        return None

    def set(self, key: str, data: Any):
        self.cache[key] = {
            "timestamp": time.time(),
            "data": data
        }
        logger.info(f"Cache SET for key: {key}")

    def clear(self):
        self.cache.clear()

kpi_cache = CacheService(ttl_seconds=60)
