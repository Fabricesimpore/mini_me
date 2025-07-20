from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# Schemas
class IntegrationStatus(BaseModel):
    name: str
    status: str  # connected, disconnected, error
    last_sync: Optional[datetime]
    data_points: int
    features: List[str]

class IntegrationConfig(BaseModel):
    integration_name: str
    settings: Dict[str, Any]

# Mock integration status
integrations_data = {
    "gmail": {
        "name": "Gmail",
        "status": "disconnected",
        "last_sync": None,
        "data_points": 0,
        "features": ["Email analysis", "Contact extraction", "Priority detection"]
    },
    "calendar": {
        "name": "Google Calendar",
        "status": "disconnected",
        "last_sync": None,
        "data_points": 0,
        "features": ["Event tracking", "Meeting analysis", "Time blocking"]
    },
    "todoist": {
        "name": "Todoist",
        "status": "disconnected",
        "last_sync": None,
        "data_points": 0,
        "features": ["Task management", "Priority tracking", "Completion analysis"]
    },
    "screen_observer": {
        "name": "Screen Observer",
        "status": "ready",
        "last_sync": None,
        "data_points": 0,
        "features": ["Activity tracking", "App usage", "Focus time analysis"]
    }
}

@router.get("/status", response_model=List[IntegrationStatus])
async def get_integrations_status():
    """Get status of all integrations"""
    return [IntegrationStatus(**data) for data in integrations_data.values()]

@router.get("/status/{integration_name}", response_model=IntegrationStatus)
async def get_integration_status(integration_name: str):
    """Get status of a specific integration"""
    if integration_name not in integrations_data:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return IntegrationStatus(**integrations_data[integration_name])

@router.post("/connect/{integration_name}")
async def connect_integration(integration_name: str):
    """Connect to an integration"""
    if integration_name not in integrations_data:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Mock connection process
    integrations_data[integration_name]["status"] = "connected"
    integrations_data[integration_name]["last_sync"] = datetime.utcnow()
    
    return {
        "status": "connected",
        "message": f"{integration_name} connected successfully",
        "next_steps": "Configure sync settings in the integration panel"
    }

@router.post("/disconnect/{integration_name}")
async def disconnect_integration(integration_name: str):
    """Disconnect from an integration"""
    if integration_name not in integrations_data:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integrations_data[integration_name]["status"] = "disconnected"
    integrations_data[integration_name]["last_sync"] = None
    
    return {"status": "disconnected", "message": f"{integration_name} disconnected"}

@router.post("/sync/{integration_name}")
async def sync_integration(integration_name: str):
    """Manually sync data from an integration"""
    if integration_name not in integrations_data:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integrations_data[integration_name]["status"] != "connected":
        raise HTTPException(status_code=400, detail="Integration not connected")
    
    # Mock sync process
    integrations_data[integration_name]["last_sync"] = datetime.utcnow()
    integrations_data[integration_name]["data_points"] += 10  # Mock data
    
    return {
        "status": "success",
        "synced_items": 10,
        "last_sync": integrations_data[integration_name]["last_sync"]
    }

@router.get("/summary")
async def get_integrations_summary():
    """Get summary of all integrations data"""
    connected = sum(1 for i in integrations_data.values() if i["status"] == "connected")
    total_data_points = sum(i["data_points"] for i in integrations_data.values())
    
    return {
        "total_integrations": len(integrations_data),
        "connected_integrations": connected,
        "total_data_points": total_data_points,
        "insights": {
            "most_active": "Gmail" if connected > 0 else None,
            "sync_health": "Good" if connected > 2 else "Needs attention",
            "recommendations": [
                "Connect more integrations for better insights",
                "Enable automatic sync for real-time updates"
            ]
        }
    }