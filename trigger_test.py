import requests
import json

# The Northbound API endpoint of your Orchestrator
URL = "http://127.0.0.1:8000/api/v1/workflows/trigger"

# !!! IMPORTANT: Paste the exact Session ID from your Server terminal here !!!
# It looks something like "zX9yV2aBcDeFgHiJ"
TARGET_AGENT_SID = "SxvaVnBruQKozmG4AAAB"

# The headers must match the adapter credentials we seeded in MongoDB
headers = {
    "Content-Type": "application/json",
    "x-api-key": "sk_live_123456789"
}

# The payload tells the server WHO to trigger, WHERE it came from, and WHAT to do
payload = {
    "target_agent_id": TARGET_AGENT_SID,
    "adapter_name": "crm_webhook_inbound",
    "workflow_name": "system_cleanup_v1"
}

print(f"Firing trigger to Orchestrator for Agent: {TARGET_AGENT_SID}...\n")

try:
    response = requests.post(URL, headers=headers, data=json.dumps(payload))
    print(f"--- API Response ---")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}\n")

    if response.status_code == 200:
        print("Success! Now quickly look at your Server and Client terminals to watch the execution!")
except Exception as e:
    print(f"Failed to connect to the API. Is the server running? Error: {e}")