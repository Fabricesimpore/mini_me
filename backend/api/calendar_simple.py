from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import OAuth handler
try:
    from integrations.calendar.calendar_oauth import calendar_oauth
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    calendar_oauth = None

# Import auth dependency
from api.auth_simple import get_current_user

router = APIRouter()

# Schemas
class CalendarStatus(BaseModel):
    connected: bool
    last_sync: Optional[datetime]
    total_events: int
    upcoming_today: int

class CalendarEvent(BaseModel):
    id: str
    title: str
    start: str
    end: str
    all_day: bool
    location: Optional[str]
    attendees_count: int
    meeting_type: str

# Check if Google credentials are configured
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_OAUTH_CONFIGURED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

@router.get("/status", response_model=CalendarStatus)
async def get_calendar_status(user = Depends(get_current_user)):
    """Get Calendar integration status"""
    user_id = user["id"]
    
    # Check if OAuth is available and user has credentials
    if OAUTH_AVAILABLE and calendar_oauth:
        credentials = calendar_oauth.get_credentials(user_id)
        if credentials and not credentials.expired:
            try:
                # Get real calendar stats
                events = calendar_oauth.fetch_events(user_id, max_results=20)
                
                # Count today's events
                today = datetime.utcnow().date()
                today_events = 0
                for event in events:
                    try:
                        event_date = datetime.fromisoformat(event['start'].replace('Z', '+00:00')).date()
                        if event_date == today:
                            today_events += 1
                    except:
                        pass
                
                return CalendarStatus(
                    connected=True,
                    last_sync=datetime.utcnow(),
                    total_events=len(events),
                    upcoming_today=today_events
                )
            except:
                pass
    
    # Fallback to disconnected state
    return CalendarStatus(
        connected=False,
        last_sync=None,
        total_events=0,
        upcoming_today=0
    )

@router.get("/auth")
async def calendar_auth(user = Depends(get_current_user)):
    """Get Calendar OAuth URL"""
    user_id = user["id"]
    
    if not GOOGLE_OAUTH_CONFIGURED:
        # Return instructions if OAuth not configured
        return {
            "auth_url": None,
            "message": "Google OAuth not configured. Please add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file. See SETUP_GOOGLE_OAUTH.md for instructions."
        }
    
    if OAUTH_AVAILABLE and calendar_oauth:
        try:
            auth_url = calendar_oauth.get_auth_url(user_id)
            return {
                "auth_url": auth_url,
                "message": "Visit the auth_url to connect your Google Calendar"
            }
        except Exception as e:
            return {
                "auth_url": None,
                "message": f"Error generating auth URL: {str(e)}"
            }
    
    # Fallback
    return {
        "auth_url": None,
        "message": "Calendar OAuth integration not available"
    }

@router.get("/callback")
async def calendar_callback(code: str, state: str):
    """Handle Calendar OAuth callback"""
    if not OAUTH_AVAILABLE or not calendar_oauth:
        raise HTTPException(status_code=500, detail="OAuth not available")
    
    try:
        # Handle the OAuth callback
        credentials = calendar_oauth.handle_callback(code, state)
        
        # Redirect back to frontend with success
        return RedirectResponse(
            url="http://localhost:5174/integrations?calendar=connected",
            status_code=302
        )
    except Exception as e:
        # Redirect with error
        return RedirectResponse(
            url=f"http://localhost:5174/integrations?calendar=error&message={str(e)}",
            status_code=302
        )

@router.post("/disconnect")
async def disconnect_calendar(user = Depends(get_current_user)):
    """Disconnect Calendar"""
    user_id = user["id"]
    
    if OAUTH_AVAILABLE and calendar_oauth:
        # Remove stored credentials
        if user_id in calendar_oauth.credentials_store:
            del calendar_oauth.credentials_store[user_id]
    
    return {"status": "disconnected", "message": "Calendar disconnected successfully"}

@router.get("/events")
async def get_calendar_events(
    days: int = 7,
    user = Depends(get_current_user)
):
    """Get upcoming calendar events"""
    user_id = user["id"]
    
    # Check if user has valid credentials
    if OAUTH_AVAILABLE and calendar_oauth:
        credentials = calendar_oauth.get_credentials(user_id)
        if credentials and not credentials.expired:
            try:
                # Get real events
                time_max = datetime.utcnow() + timedelta(days=days)
                events = calendar_oauth.fetch_events(
                    user_id, 
                    time_min=datetime.utcnow(),
                    time_max=time_max,
                    max_results=50
                )
                
                # Format for frontend
                formatted_events = []
                for event in events:
                    formatted_events.append(CalendarEvent(
                        id=event['id'],
                        title=event['summary'],
                        start=event['start'],
                        end=event['end'],
                        all_day=event['all_day'],
                        location=event.get('location'),
                        attendees_count=len(event.get('attendees', [])),
                        meeting_type=event['meeting_type']
                    ))
                
                return {
                    "events": formatted_events,
                    "total": len(formatted_events)
                }
            except Exception as e:
                print(f"Error getting events: {e}")
    
    # Return mock data if no real connection
    raise HTTPException(status_code=400, detail="Calendar not connected")

@router.get("/insights")
async def get_calendar_insights(user = Depends(get_current_user)):
    """Get calendar insights and patterns"""
    user_id = user["id"]
    
    # Check if user has valid credentials
    if OAUTH_AVAILABLE and calendar_oauth:
        credentials = calendar_oauth.get_credentials(user_id)
        if credentials and not credentials.expired:
            try:
                # Get real calendar analysis
                analysis = calendar_oauth.analyze_calendar_patterns(user_id)
                
                # Add time optimization suggestions
                suggestions = []
                
                # Check meeting density
                if analysis['total_events'] > 30:
                    suggestions.append("Consider blocking focus time between meetings")
                
                # Check for back-to-back meetings
                if analysis['busiest_hours']:
                    suggestions.append(f"Your busiest hours are {analysis['busiest_hours'][0]}:00 - consider scheduling breaks")
                
                # Check meeting types
                meeting_types = analysis['meeting_types']
                if meeting_types.get('meeting', 0) > meeting_types.get('personal', 0) * 3:
                    suggestions.append("Your calendar is meeting-heavy. Schedule personal time for deep work")
                
                return {
                    "summary": {
                        "total_events": analysis['total_events'],
                        "recurring_events": analysis['recurring_count'],
                        "busiest_hours": analysis['busiest_hours'][:3],
                        "meeting_load": "heavy" if analysis['total_events'] > 40 else "moderate" if analysis['total_events'] > 20 else "light"
                    },
                    "meeting_types": analysis['meeting_types'],
                    "insights": analysis['insights'],
                    "suggestions": suggestions,
                    "time_distribution": {
                        "daily": analysis['daily_distribution'],
                        "weekly": analysis['weekday_distribution']
                    }
                }
            except Exception as e:
                print(f"Error getting calendar insights: {e}")
    
    # Return error if no real connection
    raise HTTPException(status_code=400, detail="Calendar not connected")