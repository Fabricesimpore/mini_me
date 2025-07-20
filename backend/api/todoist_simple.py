from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# Schemas
class TodoistStatus(BaseModel):
    connected: bool
    last_sync: Optional[datetime]
    total_tasks: int
    completed_today: int

# Mock data
todoist_connected = False

@router.get("/status", response_model=TodoistStatus)
async def get_todoist_status():
    """Get Todoist integration status"""
    return TodoistStatus(
        connected=todoist_connected,
        last_sync=datetime.utcnow() if todoist_connected else None,
        total_tasks=45 if todoist_connected else 0,
        completed_today=7 if todoist_connected else 0
    )

@router.get("/auth")
async def todoist_auth():
    """Get Todoist OAuth URL"""
    return {
        "auth_url": "https://todoist.com/oauth/authorize?client_id=YOUR_CLIENT_ID&scope=data:read",
        "message": "Visit the auth_url to connect your Todoist account"
    }

@router.post("/connect")
async def connect_todoist():
    """Mock Todoist connection"""
    global todoist_connected
    todoist_connected = True
    return {"status": "connected", "message": "Todoist connected successfully"}