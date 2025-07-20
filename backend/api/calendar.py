from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.database import get_db
from core.models.user import User
from api.auth import get_current_user
from integrations.calendar.calendar_service import GoogleCalendarService
from app.services.memory_service import MemoryService
from app.services.cognitive_profile_service import CognitiveProfileService

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for OAuth states (use Redis in production)
oauth_states = {}


@router.get("/auth")
async def authorize_calendar(
    current_user: dict = Depends(get_current_user)
):
    """Get Google Calendar OAuth authorization URL"""
    try:
        service = GoogleCalendarService()
        auth_url = service.get_authorization_url()
        
        # Generate state for security
        state = str(uuid.uuid4())
        oauth_states[state] = current_user["user_id"]
        
        # Add state to auth URL
        auth_url += f"&state={state}"
        
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error getting auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth-callback")
async def oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth2 callback from Google"""
    # Verify state
    user_id = oauth_states.get(state)
    if not user_id:
        return RedirectResponse(
            url="http://localhost:3000/integrations?calendar=error&message=Invalid state",
            status_code=302
        )
    
    # Clean up state
    del oauth_states[state]
    
    try:
        service = GoogleCalendarService()
        token_data = service.handle_oauth_callback(code)
        
        # Store tokens in database
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return RedirectResponse(
                url="http://localhost:3000/integrations?calendar=error&message=User not found",
                status_code=302
            )
        
        # Update user's integrations data
        integrations_data = user.integrations_data or {}
        integrations_data['calendar'] = {
            'connected': True,
            'email': token_data['email'],
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'token_expiry': token_data['token_expiry'],
            'connected_at': datetime.utcnow().isoformat()
        }
        
        await db.execute(
            update(User).where(User.id == user.id).values(
                integrations_data=integrations_data
            )
        )
        await db.commit()
        
        # Store initial memory about calendar connection
        memory_service = MemoryService()
        await memory_service.store_memory(
            db,
            user_id=user.id,
            memory_type="procedural",
            content=f"Connected Google Calendar account: {token_data['email']}",
            source="calendar_integration",
            metadata={
                "integration": "calendar",
                "action": "connected",
                "email": token_data['email']
            }
        )
        
        return RedirectResponse(
            url=f"http://localhost:3000/integrations?calendar=connected&email={token_data['email']}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"http://localhost:3000/integrations?calendar=error&message={str(e)}",
            status_code=302
        )


@router.get("/status")
async def get_calendar_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Google Calendar connection status"""
    user_id = uuid.UUID(current_user["user_id"])
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.integrations_data:
        return {"connected": False}
    
    calendar_data = user.integrations_data.get('calendar', {})
    
    if not calendar_data.get('connected'):
        return {"connected": False}
    
    try:
        # Try to get calendar list to verify connection
        service = GoogleCalendarService()
        service.set_credentials(calendar_data)
        calendars = service.get_calendar_list()
        
        return {
            "connected": True,
            "email": calendar_data.get('email'),
            "calendars_count": len(calendars),
            "connected_at": calendar_data.get('connected_at')
        }
    except Exception as e:
        logger.error(f"Error checking calendar status: {str(e)}")
        return {"connected": False, "error": str(e)}


@router.get("/calendars")
async def get_calendars(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of user's calendars"""
    user_id = uuid.UUID(current_user["user_id"])
    
    # Get user's calendar credentials
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.integrations_data or not user.integrations_data.get('calendar', {}).get('connected'):
        raise HTTPException(status_code=403, detail="Calendar not connected")
    
    try:
        service = GoogleCalendarService()
        service.set_credentials(user.integrations_data['calendar'])
        calendars = service.get_calendar_list()
        
        return {"calendars": calendars}
    except Exception as e:
        logger.error(f"Error getting calendars: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_calendar(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze calendar patterns and update cognitive profile"""
    user_id = uuid.UUID(current_user["user_id"])
    max_events = request.get('max_events', 500)
    
    # Get user's calendar credentials
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.integrations_data or not user.integrations_data.get('calendar', {}).get('connected'):
        raise HTTPException(status_code=403, detail="Calendar not connected")
    
    try:
        # Analyze calendar
        service = GoogleCalendarService()
        service.set_credentials(user.integrations_data['calendar'])
        analysis = service.analyze_calendar_patterns(max_events=max_events)
        
        # Store insights as memories
        memory_service = MemoryService()
        cognitive_service = CognitiveProfileService()
        
        # Store time patterns
        await memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="semantic",
            content=f"Calendar analysis shows peak productivity hours at {analysis['time_patterns'].get('typical_start_time', '9:00 AM')}",
            source="calendar_analysis",
            metadata={
                "analysis_type": "time_patterns",
                "patterns": analysis['time_patterns']
            }
        )
        
        # Store meeting patterns
        if analysis['meeting_patterns']['top_collaborators']:
            top_collaborator = analysis['meeting_patterns']['top_collaborators'][0]
            await memory_service.store_memory(
                db,
                user_id=user_id,
                memory_type="social",
                content=f"Frequently collaborates with {top_collaborator['email']} ({top_collaborator['meetings']} meetings)",
                source="calendar_analysis",
                metadata={
                    "relationship_type": "professional",
                    "collaborators": analysis['meeting_patterns']['top_collaborators']
                }
            )
        
        # Store work-life balance insights
        balance_score = analysis['work_life_balance']['work_life_balance_score']
        await memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="semantic",
            content=f"Work-life balance score: {balance_score:.1f}/100. Work hours: {analysis['work_life_balance']['work_hours_percentage']:.1f}%",
            source="calendar_analysis",
            metadata={
                "balance_metrics": analysis['work_life_balance']
            }
        )
        
        # Update cognitive profile based on calendar patterns
        profile_updates = {}
        
        # High conscientiousness if many advance scheduled events
        if analysis['scheduling_habits']['average_advance_scheduling_days'] > 7:
            profile_updates['conscientiousness'] = 0.7
        
        # Extraversion based on meeting frequency
        total_events = analysis['events_analyzed']
        meeting_ratio = analysis['event_categories']['meetings'] / total_events if total_events > 0 else 0
        if meeting_ratio > 0.5:
            profile_updates['extraversion'] = 0.7
        elif meeting_ratio < 0.2:
            profile_updates['extraversion'] = 0.3
        
        # Update profile if we have insights
        if profile_updates:
            await cognitive_service.update_profile_from_behaviors(
                db, user_id, profile_updates
            )
        
        return {
            "status": "success",
            "events_analyzed": analysis['events_analyzed'],
            "insights": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect_calendar(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect Google Calendar"""
    user_id = uuid.UUID(current_user["user_id"])
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user and user.integrations_data and 'calendar' in user.integrations_data:
        integrations_data = user.integrations_data
        del integrations_data['calendar']
        
        await db.execute(
            update(User).where(User.id == user_id).values(
                integrations_data=integrations_data
            )
        )
        await db.commit()
        
        # Store memory about disconnection
        memory_service = MemoryService()
        await memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="procedural",
            content="Disconnected Google Calendar integration",
            source="calendar_integration",
            metadata={
                "integration": "calendar",
                "action": "disconnected"
            }
        )
    
    return {"status": "disconnected"}


@router.get("/upcoming")
async def get_upcoming_events(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming events for the next N days"""
    user_id = uuid.UUID(current_user["user_id"])
    
    # Get user's calendar credentials
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.integrations_data or not user.integrations_data.get('calendar', {}).get('connected'):
        raise HTTPException(status_code=403, detail="Calendar not connected")
    
    try:
        from datetime import timedelta
        import pytz
        
        service = GoogleCalendarService()
        service.set_credentials(user.integrations_data['calendar'])
        
        # Get events for the next N days
        time_min = datetime.now(pytz.UTC)
        time_max = time_min + timedelta(days=days)
        
        events = service.get_events(
            time_min=time_min,
            time_max=time_max,
            max_results=50
        )
        
        # Format events for frontend
        formatted_events = []
        for event in events:
            formatted_event = {
                "id": event.get('id'),
                "summary": event.get('summary', 'No title'),
                "start": event.get('start'),
                "end": event.get('end'),
                "location": event.get('location'),
                "attendees_count": len(event.get('attendees', [])),
                "is_recurring": bool(event.get('recurringEventId')),
                "meeting_link": event.get('hangoutLink')
            }
            formatted_events.append(formatted_event)
        
        return {
            "events": formatted_events,
            "count": len(formatted_events),
            "time_range": {
                "start": time_min.isoformat(),
                "end": time_max.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting upcoming events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))