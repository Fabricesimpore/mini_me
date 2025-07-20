from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# Schemas
class GmailStatus(BaseModel):
    connected: bool
    last_sync: Optional[datetime]
    total_emails: int
    unread_count: int

class EmailSummary(BaseModel):
    id: str
    subject: str
    from_email: str
    preview: str
    importance: str  # high, medium, low
    received_at: datetime
    has_attachments: bool

# Mock data
gmail_connected = False

@router.get("/status", response_model=GmailStatus)
async def get_gmail_status():
    """Get Gmail integration status"""
    return GmailStatus(
        connected=gmail_connected,
        last_sync=datetime.utcnow() if gmail_connected else None,
        total_emails=1247 if gmail_connected else 0,
        unread_count=23 if gmail_connected else 0
    )

@router.get("/auth")
async def gmail_auth():
    """Get Gmail OAuth URL"""
    return {
        "auth_url": "https://accounts.google.com/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/api/gmail/callback&scope=gmail.readonly",
        "message": "Visit the auth_url to connect your Gmail account"
    }

@router.post("/connect")
async def connect_gmail():
    """Mock Gmail connection"""
    global gmail_connected
    gmail_connected = True
    return {"status": "connected", "message": "Gmail connected successfully"}

@router.post("/disconnect")
async def disconnect_gmail():
    """Disconnect Gmail"""
    global gmail_connected
    gmail_connected = False
    return {"status": "disconnected"}

@router.get("/insights")
async def get_email_insights():
    """Get email insights"""
    if not gmail_connected:
        raise HTTPException(status_code=400, detail="Gmail not connected")
    
    return {
        "summary": {
            "total_this_week": 156,
            "response_rate": 0.78,
            "avg_response_time_hours": 2.5
        },
        "top_senders": [
            {"email": "team@work.com", "count": 45},
            {"email": "notifications@github.com", "count": 32}
        ],
        "categories": {
            "work": 89,
            "personal": 23,
            "newsletters": 44
        },
        "insights": [
            "You respond fastest to emails from your team",
            "Consider unsubscribing from 12 inactive newsletters",
            "Your email volume peaks on Mondays and Thursdays"
        ]
    }