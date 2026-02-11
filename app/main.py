from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.dependencies import realtime_manager
from app.routers import ai, insights, schedule, tasks

app = FastAPI(title="AI Productivity OS API", version="0.1.0")
app.include_router(tasks.router)
app.include_router(ai.router)
app.include_router(insights.router)
app.include_router(schedule.router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/v1/realtime")
async def realtime_updates(websocket: WebSocket) -> None:
    await realtime_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_manager.disconnect(websocket)
