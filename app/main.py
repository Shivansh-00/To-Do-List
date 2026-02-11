from __future__ import annotations

import logging
import traceback
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.database import init_db
from app.dependencies import realtime_manager
from app.routers import ai, auth, insights, schedule, tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Resolve project root (works in any deployment CWD)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AI Productivity OS", version="1.0.0", redirect_slashes=False)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: always return JSON, never plain-text 500."""
    logger.error(f"Unhandled error on {request.method} {request.url}: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers FIRST (before static mount)
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(ai.router)
app.include_router(insights.router)
app.include_router(schedule.router)


@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info(f"Static dir: {STATIC_DIR} (exists={STATIC_DIR.exists()})")
    logger.info(f"DB dir: {BASE_DIR}")


@app.get("/")
async def serve_frontend():
    return FileResponse(str(STATIC_DIR / "index.html"))


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


# Mount static LAST so it doesn't shadow API routes
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
