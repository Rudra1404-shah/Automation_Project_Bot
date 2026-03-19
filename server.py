import uvicorn
from fastapi import FastAPI,WebSocket
from starlette.websockets import WebSocketDisconnect

app = FastAPI()
@app.websocket("/ws")
async def websocket_endpiont(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()

            if "bye" in data or "quit" in data:
                await ws.send_text("Closing connection")
                await ws.close(code=1000, reason="Server requested close")
                break
            await ws.send_text(f"I got your request: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
if __name__ == "__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)