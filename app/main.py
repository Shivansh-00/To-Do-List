from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.dependencies import realtime_manager
from app.routers import ai, auth, insights, schedule, tasks

app = FastAPI(title="AI Productivity OS", version="1.0.0")

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(ai.router)
app.include_router(insights.router)
app.include_router(schedule.router)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


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
