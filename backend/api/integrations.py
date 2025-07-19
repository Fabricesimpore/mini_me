from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.auth import get_current_user

router = APIRouter()


@router.get("/available")
async def get_available_integrations():
    """Get list of available integrations"""
    integrations = [
        {
            "id": "gmail",
            "name": "Gmail",
            "description": "Access and analyze your Gmail emails",
            "status": "available",
            "required_scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
        },
        {
            "id": "whatsapp",
            "name": "WhatsApp",
            "description": "Connect to WhatsApp Web for message analysis",
            "status": "available",
            "required_scopes": []
        },
        {
            "id": "calendar",
            "name": "Google Calendar",
            "description": "Sync your calendar events and patterns",
            "status": "available",
            "required_scopes": ["https://www.googleapis.com/auth/calendar.readonly"]
        },
        {
            "id": "browser",
            "name": "Browser Extension",
            "description": "Track browsing patterns and web interactions",
            "status": "available",
            "required_scopes": []
        }
    ]
    
    return {"integrations": integrations}


@router.post("/connect/{integration_id}")
async def connect_integration(
    integration_id: str,
    auth_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Connect a new integration"""
    user_id = current_user["user_id"]
    
    # TODO: Implement actual integration connection logic
    
    if integration_id not in ["gmail", "whatsapp", "calendar", "browser"]:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {
        "status": "connected",
        "integration_id": integration_id,
        "user_id": user_id,
        "connected_at": datetime.utcnow()
    }


@router.delete("/disconnect/{integration_id}")
async def disconnect_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect an integration"""
    user_id = current_user["user_id"]
    
    # TODO: Implement disconnection logic
    
    return {
        "status": "disconnected",
        "integration_id": integration_id,
        "user_id": user_id,
        "disconnected_at": datetime.utcnow()
    }


@router.get("/status")
async def get_integration_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get status of all user integrations"""
    user_id = current_user["user_id"]
    
    # TODO: Fetch from database
    
    status = {
        "gmail": {
            "connected": True,
            "last_sync": "2024-01-18T10:00:00",
            "emails_analyzed": 1250,
            "status": "active"
        },
        "browser": {
            "connected": True,
            "last_activity": "2024-01-18T14:30:00",
            "pages_tracked": 450,
            "status": "active"
        },
        "whatsapp": {
            "connected": False,
            "status": "not_connected"
        },
        "calendar": {
            "connected": False,
            "status": "not_connected"
        }
    }
    
    return {
        "user_id": user_id,
        "integrations": status
    }


@router.post("/sync/{integration_id}")
async def sync_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger sync for an integration"""
    user_id = current_user["user_id"]
    
    # TODO: Trigger sync process
    
    return {
        "status": "sync_started",
        "integration_id": integration_id,
        "user_id": user_id,
        "started_at": datetime.utcnow()
    }