from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import os

# Import auth dependency
from api.auth_simple import get_current_user

router = APIRouter()

# Schemas
class OutlookStatus(BaseModel):
    connected: bool
    last_sync: Optional[datetime]
    total_emails: int
    unread_count: int

class OutlookEvent(BaseModel):
    id: str
    subject: str
    start: datetime
    end: datetime
    location: Optional[str]
    attendees_count: int

# Check if Microsoft credentials are configured
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_OAUTH_CONFIGURED = bool(MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET)

# In-memory connection state (in production use database)
outlook_connections = {}

@router.get("/status", response_model=OutlookStatus)
async def get_outlook_status(user = Depends(get_current_user)):
    """Get Outlook integration status"""
    user_id = user["id"]
    
    if user_id in outlook_connections and outlook_connections[user_id]:
        return OutlookStatus(
            connected=True,
            last_sync=datetime.utcnow(),
            total_emails=856,
            unread_count=42
        )
    
    return OutlookStatus(
        connected=False,
        last_sync=None,
        total_emails=0,
        unread_count=0
    )

@router.get("/auth")
async def outlook_auth(user = Depends(get_current_user)):
    """Get Outlook OAuth URL"""
    if not MICROSOFT_OAUTH_CONFIGURED:
        return {
            "auth_url": None,
            "message": "Microsoft OAuth not configured. Add MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET to your .env file."
        }
    
    # Microsoft OAuth URL
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={MICROSOFT_CLIENT_ID}&response_type=code&redirect_uri=http://localhost:8000/api/outlook/callback&scope=https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Calendars.Read&response_mode=query"
    
    return {
        "auth_url": auth_url,
        "message": "Visit the auth_url to connect your Outlook account"
    }

@router.get("/callback")
async def outlook_callback(code: str, state: Optional[str] = None):
    """Handle Outlook OAuth callback"""
    # In production, exchange code for tokens and store securely
    # For now, mock the connection
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="http://localhost:5174/integrations?outlook=connected",
        status_code=302
    )

@router.post("/connect")
async def connect_outlook(user = Depends(get_current_user)):
    """Mock Outlook connection for demo"""
    user_id = user["id"]
    outlook_connections[user_id] = True
    return {"status": "connected", "message": "Outlook connected successfully (demo mode)"}

@router.post("/disconnect")
async def disconnect_outlook(user = Depends(get_current_user)):
    """Disconnect Outlook"""
    user_id = user["id"]
    if user_id in outlook_connections:
        del outlook_connections[user_id]
    return {"status": "disconnected", "message": "Outlook disconnected successfully"}

@router.get("/emails/summary")
async def get_email_summary(user = Depends(get_current_user)):
    """Get Outlook email summary"""
    user_id = user["id"]
    
    if user_id not in outlook_connections or not outlook_connections[user_id]:
        raise HTTPException(status_code=400, detail="Outlook not connected")
    
    return {
        "folders": {
            "inbox": {"total": 456, "unread": 23},
            "sent": {"total": 234, "unread": 0},
            "drafts": {"total": 5, "unread": 5},
            "deleted": {"total": 89, "unread": 2}
        },
        "recent_senders": [
            {"email": "manager@company.com", "count": 45},
            {"email": "team@project.com", "count": 32},
            {"email": "client@external.com", "count": 28}
        ],
        "insights": [
            "You receive most emails on Monday mornings",
            "Average response time: 2.5 hours",
            "23% of emails are from external contacts"
        ]
    }

@router.get("/calendar/events")
async def get_calendar_events(
    days: int = 7,
    user = Depends(get_current_user)
):
    """Get Outlook calendar events"""
    user_id = user["id"]
    
    if user_id not in outlook_connections or not outlook_connections[user_id]:
        raise HTTPException(status_code=400, detail="Outlook not connected")
    
    # Mock events
    events = []
    from datetime import timedelta
    base_time = datetime.utcnow()
    
    events.append(OutlookEvent(
        id="1",
        subject="Team Standup",
        start=base_time.replace(hour=9, minute=0),
        end=base_time.replace(hour=9, minute=30),
        location="Teams Meeting",
        attendees_count=5
    ))
    
    events.append(OutlookEvent(
        id="2",
        subject="Project Review",
        start=base_time.replace(hour=14, minute=0),
        end=base_time.replace(hour=15, minute=0),
        location="Conference Room A",
        attendees_count=8
    ))
    
    return {
        "events": events,
        "total": len(events)
    }

@router.get("/insights")
async def get_outlook_insights(user = Depends(get_current_user)):
    """Get combined Outlook insights"""
    user_id = user["id"]
    
    if user_id not in outlook_connections or not outlook_connections[user_id]:
        raise HTTPException(status_code=400, detail="Outlook not connected")
    
    return {
        "email_patterns": {
            "peak_hours": [9, 10, 11, 14, 15],
            "busiest_day": "Monday",
            "avg_emails_per_day": 45
        },
        "meeting_patterns": {
            "avg_meetings_per_week": 18,
            "most_common_duration": 30,
            "back_to_back_meetings": 6
        },
        "productivity_score": {
            "email_efficiency": 78,
            "meeting_optimization": 65,
            "focus_time_available": 42
        },
        "recommendations": [
            "Block 2-4 PM for focused work",
            "Consider batching email responses",
            "5 recurring meetings could be emails"
        ]
    }