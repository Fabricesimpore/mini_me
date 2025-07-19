from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict

from api import auth, health, behavioral, memory, integrations, chat
from core.database import init_db
from core.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager
manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Digital Twin Platform...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Digital Twin Platform...")


# Create FastAPI app
app = FastAPI(
    title="Digital Twin Platform",
    description="A platform that creates a true digital twin of you",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(behavioral.router, prefix="/api/behavioral", tags=["behavioral"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time behavioral data streaming"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Process behavioral data in real-time
            await manager.process_behavioral_data(user_id, data)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")


@app.get("/")
async def root():
    return {
        "message": "Welcome to Digital Twin Platform",
        "status": "operational",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)