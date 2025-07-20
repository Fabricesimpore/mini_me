from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()

# Schemas
class CalendarStatus(BaseModel):
    connected: bool
    last_sync: Optional[datetime]
    total_events: int
    upcoming_events: int

class Event(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    attendees: List[str]
    location: Optional[str]
    meeting_type: str  # meeting, focus_time, personal

# Mock data
calendar_connected = False

@router.get("/status", response_model=CalendarStatus)
async def get_calendar_status():
    """Get Calendar integration status"""
    return CalendarStatus(
        connected=calendar_connected,
        last_sync=datetime.utcnow() if calendar_connected else None,
        total_events=89 if calendar_connected else 0,
        upcoming_events=12 if calendar_connected else 0
    )

@router.get("/auth")
async def calendar_auth():
    """Get Calendar OAuth URL"""
    return {
        "auth_url": "https://accounts.google.com/oauth2/auth?client_id=YOUR_CLIENT_ID&scope=calendar.readonly",
        "message": "Visit the auth_url to connect your Google Calendar"
    }

@router.post("/connect")
async def connect_calendar():
    """Mock Calendar connection"""
    global calendar_connected
    calendar_connected = True
    return {"status": "connected", "message": "Calendar connected successfully"}

@router.get("/insights")
async def get_calendar_insights():
    """Get calendar insights"""
    if not calendar_connected:
        raise HTTPException(status_code=400, detail="Calendar not connected")
    
    return {
        "meeting_stats": {
            "total_hours_this_week": 12.5,
            "average_meeting_duration": 45,
            "meeting_free_blocks": 8
        },
        "patterns": [
            "Most meetings scheduled on Tuesday and Thursday",
            "Average 2.5 hours of focus time per day",
            "Meeting load increased by 20% this month"
        ],
        "recommendations": [
            "Block 9-11 AM for deep work",
            "Consider declining recurring meetings with low engagement",
            "Schedule breaks between back-to-back meetings"
        ]
    }