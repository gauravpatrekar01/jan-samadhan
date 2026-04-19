from db import db
import logging

logger = logging.getLogger(__name__)

async def init_db_indexes():
    """Create indexes for optimized performance."""
    try:
        collection = db.get_collection("complaints")
        
        # Core search indexes
        logger.info("Creating indexes for complaints collection...")
        collection.create_index("status")
        collection.create_index("priority")
        collection.create_index("region")
        collection.create_index("citizen_email")
        collection.create_index("assigned_officer")
        collection.create_index("grievanceID", unique=True)
        
        # Production readiness indexes
        collection.create_index("sla_deadline")
        collection.create_index("assigned_to_ngo")
        
        # Geospatial index (using separate field to avoid conflict with human-readable location string)
        collection.create_index([("location_geo", "2dsphere")], sparse=True)
        
        # Audit logs indexes
        audit_collection = db.get_collection("audit_logs")
        audit_collection.create_index("timestamp")
        audit_collection.create_index("actor_email")
        
        # Users indexes
        users_collection = db.get_collection("users")
        users_collection.create_index("email", unique=True)
        users_collection.create_index("role")
        
        logger.info("Successfully created all database indexes.")
        return True
    except Exception as e:
        logger.error(f"Failed to create indexes: {str(e)}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db_indexes())
