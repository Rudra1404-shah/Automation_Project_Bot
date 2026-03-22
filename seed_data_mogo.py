from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def seed_database():
    # Connect to the local MongoDB instance
    client = MongoClient("mongodb://localhost:27017/")
    db = client["orchestrator_db"]

    # --- 1. Seed the Adapter (Authentication) ---
    adapters_collection = db["adapters"]

    # Clear existing data so we don't create duplicates if you run this twice
    adapters_collection.delete_many({})

    adapter_data = {
        "adapter_name": "crm_webhook_inbound",
        "api_key": "sk_live_123456789",
        "allowed_workflows": ["system_cleanup_v1"]
    }
    adapters_collection.insert_one(adapter_data)
    logger.info("Successfully seeded 'adapters' collection.")

    # --- 2. Seed the Workflow (The JSON Payload Blueprint) ---
    workflows_collection = db["workflows"]
    workflows_collection.delete_many({})

    workflow_data = {
        "workflow_name": "system_cleanup_v1",
        "description": "Standard temp and cookie clearance.",
        "steps": [
            {
                "step_order": 1,
                "action": "clear_temp_files",
                "critical": True
            },
            {
                "step_order": 2,
                "action": "clear_cookies",
                "critical": False
            }
        ]
    }
    workflows_collection.insert_one(workflow_data)
    logger.info("Successfully seeded 'workflows' collection.")


if __name__ == "__main__":
    try:
        logger.info("Starting database seed...")
        seed_database()
        logger.info("Database seed complete! You are ready to run the Orchestrator.")
    except Exception as e:
        logger.error(f"Failed to seed database. Is MongoDB running locally? Error: {e}")