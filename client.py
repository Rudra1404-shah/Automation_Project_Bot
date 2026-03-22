import socketio
import asyncio
import win32api
import os
import shutil
import logging
import traceback
from rich.logging import RichHandler
# --- Production Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)
logger = logging.getLogger(__name__)

# --- Initialize Socket.IO Client ---
sio = socketio.AsyncClient()


# --- System Automation Functions ---
def clear_temp_files():
    """Uses win32api to locate and clear the Windows Temp directory."""
    try:
        temp_path = win32api.GetTempPath()
        logger.info(f"Locating Temp directory at: {temp_path}")

        deleted = 0
        failed = 0

        for item in os.listdir(temp_path):
            item_path = os.path.join(temp_path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                deleted += 1
            except Exception:
                # Some files are locked by Windows. We skip them silently.
                failed += 1

        return f"Success: Deleted {deleted} items. Skipped {failed} locked items."
    except Exception as e:
        raise RuntimeError(f"Failed to clear temp directory: {e}")


def clear_cookies():
    """Mock function for clearing cookies."""
    try:
        logger.info("Locating and clearing browser cookies...")
        return "Success: Cleared system and browser cookies."
    except Exception as e:
        raise RuntimeError(f"Failed to clear cookies: {e}")


# --- Dispatch Dictionary ---
ACTION_ROUTER = {
    "clear_temp_files": clear_temp_files,
    "clear_cookies": clear_cookies
}


# --- Socket.IO Event Handlers ---
@sio.event
async def connect():
    logger.info("Successfully connected to the Orchestrator.")


@sio.event
async def disconnect():
    logger.info("Disconnected from the Orchestrator.")


@sio.event
async def execute_workflow(payload):
    job_id = payload.get("job_id")
    steps = payload.get("steps", [])

    logger.info(f"Received Workflow '{payload.get('workflow_name')}' | Job ID: {job_id}")

    for step in steps:
        action_name = step.get("action")
        step_order = step.get("step_order")

        # Default response template
        response = {
            "job_id": job_id,
            "step_order": step_order,
            "action": action_name,
            "status_code": 500,
            "status": "error",
            "message": "Unknown error",
            "error_details": None
        }

        try:
            logger.info(f"Executing Step {step_order}: {action_name}")

            # Find the function in our router and run it
            func_to_run = ACTION_ROUTER.get(action_name)
            if not func_to_run:
                raise ValueError(f"Action '{action_name}' is not recognized.")

            success_message = await asyncio.to_thread(func_to_run)

            # Update response on success
            response["status_code"] = 200
            response["status"] = "success"
            response["message"] = success_message

        except Exception as e:
            response["status_code"] = 500
            response["message"] = str(e)
            response["error_details"] = traceback.format_exc()
            logger.error(f"Failed step {action_name}: {e}")

            if step.get("critical"):
                logger.error("Critical step failed. Halting workflow.")
                await sio.emit('step_result', response)
                break

        finally:
            # Send the result back to the server
            await sio.emit('step_result', response)
            await asyncio.sleep(1)  # Small buffer


# --- Client Startup ---
async def main():
    try:
        # Connect to the local server you just started
        await sio.connect('http://127.0.0.1:8000')
        await sio.wait()
    except Exception as e:
        logger.error(f"Connection failed: {e}")


if __name__ == '__main__':
    asyncio.run(main())