import asyncio
import websockets
async def test_client():
    uri = 'ws://127.0.0.1:8000/ws'
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello FastAPI Server, My Girlfriend's Name is Palak.")
        response = await websocket.recv()
        print("Server Repiled",response)
asyncio.run(test_client())