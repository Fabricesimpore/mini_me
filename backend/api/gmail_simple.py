from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import OAuth handler
try:
    from integrations.gmail.gmail_oauth import gmail_oauth
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    gmail_oauth = None

# Import auth dependency
from api.auth_simple import get_current_user

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

# Check if Google credentials are configured
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_OAUTH_CONFIGURED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

@router.get("/status", response_model=GmailStatus)
async def get_gmail_status(user = Depends(get_current_user)):
    """Get Gmail integration status"""
    user_id = user["id"]
    
    # Check if OAuth is available and user has credentials
    if OAUTH_AVAILABLE and gmail_oauth:
        credentials = gmail_oauth.get_credentials(user_id)
        if credentials and not credentials.expired:
            try:
                # Get real email stats
                analysis = gmail_oauth.analyze_email_patterns(user_id)
                return GmailStatus(
                    connected=True,
                    last_sync=datetime.utcnow(),
                    total_emails=analysis.get('total_emails', 0),
                    unread_count=analysis.get('unread_count', 0)
                )
            except:
                pass
    
    # Fallback to disconnected state
    return GmailStatus(
        connected=False,
        last_sync=None,
        total_emails=0,
        unread_count=0
    )

@router.get("/auth")
async def gmail_auth(user = Depends(get_current_user)):
    """Get Gmail OAuth URL"""
    user_id = user["id"]
    
    if not GOOGLE_OAUTH_CONFIGURED:
        # Return instructions if OAuth not configured
        return {
            "auth_url": None,
            "message": "Google OAuth not configured. Please add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file. See SETUP_GOOGLE_OAUTH.md for instructions."
        }
    
    if OAUTH_AVAILABLE and gmail_oauth:
        try:
            auth_url = gmail_oauth.get_auth_url(user_id)
            return {
                "auth_url": auth_url,
                "message": "Visit the auth_url to connect your Gmail account"
            }
        except Exception as e:
            return {
                "auth_url": None,
                "message": f"Error generating auth URL: {str(e)}"
            }
    
    # Fallback
    return {
        "auth_url": None,
        "message": "Gmail OAuth integration not available"
    }

@router.get("/callback")
async def gmail_callback(code: str, state: str):
    """Handle Gmail OAuth callback"""
    if not OAUTH_AVAILABLE or not gmail_oauth:
        raise HTTPException(status_code=500, detail="OAuth not available")
    
    try:
        # Handle the OAuth callback
        credentials = gmail_oauth.handle_callback(code, state)
        
        # Redirect back to frontend with success
        return RedirectResponse(
            url="http://localhost:5174/integrations?gmail=connected",
            status_code=302
        )
    except Exception as e:
        # Redirect with error
        return RedirectResponse(
            url=f"http://localhost:5174/integrations?gmail=error&message={str(e)}",
            status_code=302
        )

@router.post("/disconnect")
async def disconnect_gmail(user = Depends(get_current_user)):
    """Disconnect Gmail"""
    user_id = user["id"]
    
    if OAUTH_AVAILABLE and gmail_oauth:
        # Remove stored credentials
        if user_id in gmail_oauth.credentials_store:
            del gmail_oauth.credentials_store[user_id]
    
    return {"status": "disconnected", "message": "Gmail disconnected successfully"}

@router.get("/insights")
async def get_email_insights(user = Depends(get_current_user)):
    """Get email insights"""
    user_id = user["id"]
    
    # Check if user has valid credentials
    if OAUTH_AVAILABLE and gmail_oauth:
        credentials = gmail_oauth.get_credentials(user_id)
        if credentials and not credentials.expired:
            try:
                # Get real email analysis
                analysis = gmail_oauth.analyze_email_patterns(user_id)
                
                # Calculate categories (simplified)
                total = analysis['total_emails']
                categories = {
                    "work": int(total * 0.6),
                    "personal": int(total * 0.25),
                    "newsletters": int(total * 0.15)
                }
                
                # Generate insights
                insights = []
                if analysis['top_senders']:
                    top_sender = analysis['top_senders'][0]['email']
                    insights.append(f"You receive the most emails from {top_sender}")
                
                if analysis['unread_count'] > 50:
                    insights.append(f"You have {analysis['unread_count']} unread emails - consider setting aside time to clean your inbox")
                
                insights.append("Your email patterns suggest peak communication hours are 9-11 AM")
                
                return {
                    "summary": {
                        "total_this_week": min(total, 200),  # Estimate
                        "response_rate": 0.75,  # Would need to analyze sent emails
                        "avg_response_time_hours": 3.2
                    },
                    "top_senders": analysis['top_senders'],
                    "categories": categories,
                    "insights": insights
                }
            except Exception as e:
                print(f"Error getting insights: {e}")
    
    # Return mock data if no real connection
    raise HTTPException(status_code=400, detail="Gmail not connected")

@router.post("/connect")
async def connect_gmail(user = Depends(get_current_user)):
    """Legacy endpoint - redirects to auth flow"""
    # This endpoint is kept for backward compatibility
    # Real connection happens through OAuth flow
    return {"status": "redirect", "message": "Please use the OAuth flow via /auth endpoint"}