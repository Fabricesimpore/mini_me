from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()

# Schemas
class ScreenObserverStatus(BaseModel):
    active: bool
    started_at: Optional[datetime]
    screenshots_today: int
    storage_used_mb: float

class ActivitySummary(BaseModel):
    app_name: str
    time_spent_minutes: int
    category: str  # productivity, communication, entertainment, etc
    productivity_score: float

# Mock data
observer_active = False
observer_start_time = None

@router.get("/status", response_model=ScreenObserverStatus)
async def get_screen_observer_status():
    """Get Screen Observer status"""
    return ScreenObserverStatus(
        active=observer_active,
        started_at=observer_start_time,
        screenshots_today=127 if observer_active else 0,
        storage_used_mb=245.3 if observer_active else 0
    )

@router.post("/start")
async def start_screen_observer():
    """Start screen observation"""
    global observer_active, observer_start_time
    observer_active = True
    observer_start_time = datetime.utcnow()
    return {
        "status": "started",
        "message": "Screen observation started",
        "privacy_note": "Only app usage patterns are tracked, not content"
    }

@router.post("/stop")
async def stop_screen_observer():
    """Stop screen observation"""
    global observer_active, observer_start_time
    observer_active = False
    observer_start_time = None
    return {"status": "stopped"}

@router.get("/activity-summary", response_model=List[ActivitySummary])
async def get_activity_summary(hours: int = 24):
    """Get activity summary for the past N hours"""
    if not observer_active:
        raise HTTPException(status_code=400, detail="Screen observer not active")
    
    return [
        ActivitySummary(
            app_name="VS Code",
            time_spent_minutes=180,
            category="productivity",
            productivity_score=0.95
        ),
        ActivitySummary(
            app_name="Chrome",
            time_spent_minutes=120,
            category="mixed",
            productivity_score=0.70
        ),
        ActivitySummary(
            app_name="Slack",
            time_spent_minutes=45,
            category="communication",
            productivity_score=0.60
        ),
        ActivitySummary(
            app_name="Terminal",
            time_spent_minutes=60,
            category="productivity",
            productivity_score=0.90
        )
    ]

@router.get("/focus-score")
async def get_focus_score():
    """Get current focus score based on app switching patterns"""
    if not observer_active:
        raise HTTPException(status_code=400, detail="Screen observer not active")
    
    return {
        "current_score": 0.82,
        "trend": "improving",
        "distractions_last_hour": 3,
        "focus_sessions_today": 5,
        "longest_focus_minutes": 87,
        "recommendations": [
            "Your focus is best in the morning - protect this time",
            "Consider using website blockers during deep work",
            "Take a 5-minute break every 45 minutes"
        ]
    }