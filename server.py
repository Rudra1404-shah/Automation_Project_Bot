import logging
import uuid
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import socketio
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from rich.logging import RichHandler
# --- 1. Production Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)
logger = logging.getLogger(__name__)

# --- 2. FastAPI & Socket.IO Initialization ---
app = FastAPI(title="Dynamic Agent Orchestrator")
# Using 'asgi' mode so it shares the same server as FastAPI
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# --- 3. Database Connection ---
db_client = None
db = None

@app.on_event("startup")
async def startup_db_client():
    global db_client, db
    try:
        db_client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = db_client["orchestrator_db"]
        logger.info("Successfully connected to MongoDB.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    if db_client:
        db_client.close()

# --- 4. API Models ---
class TriggerRequest(BaseModel):
    target_agent_id: str
    adapter_name: str
    workflow_name: str

# --- 5. The REST API (Northbound) ---
@app.post("/api/v1/workflows/trigger")
async def trigger_workflow(
    payload: TriggerRequest,
    x_api_key: str = Header(...)
):
    logger.info(f"Incoming request via adapter '{payload.adapter_name}'")

    # Check the 'adapters' collection you seeded
    adapter_doc = await db["adapters"].find_one({"adapter_name": payload.adapter_name})
    if not adapter_doc or adapter_doc.get("api_key") != x_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    # Check the 'workflows' collection you seeded
    workflow_doc = await db["workflows"].find_one({"workflow_name": payload.workflow_name})
    if not workflow_doc:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    # Construct the payload to send to the Agent
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    execution_payload = {
        "job_id": job_id,
        "workflow_name": workflow_doc["workflow_name"],
        "steps": workflow_doc["steps"]
    }

    # Command the Agent via Socket.IO
    try:
        await sio.emit('execute_workflow', execution_payload, to=payload.target_agent_id)
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        logger.error(f"Socket.IO Emit Failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to reach Agent.")

# --- 6. The Socket.IO Events (Southbound) ---
@sio.event
async def connect(sid, environ):
    logger.info(f"Agent Connected! Session ID: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Agent Disconnected: {sid}")

@sio.event
async def step_result(sid, data):
    logger.info(f"Agent {sid} reported result: {data}")

# --- 7. Server Startup ---
if __name__ == '__main__':
    logger.info("Booting up the Orchestrator...")
    uvicorn.run("server:socket_app", host="127.0.0.1", port=8000)