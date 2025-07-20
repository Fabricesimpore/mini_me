from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.auth import get_current_user
from services.screen_observer.screen_capture_service import ScreenCaptureService
from services.screen_observer.activity_analyzer import ActivityAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)

# Global instances
screen_service = ScreenCaptureService()
activity_analyzer = ActivityAnalyzer()
active_captures = {}  # user_id -> task mapping


@router.post("/start")
async def start_screen_capture(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start screen capture for the current user"""
    user_id = current_user["user_id"]
    
    # Check if already capturing
    if user_id in active_captures:
        return {"status": "already_running", "message": "Screen capture is already active"}
    
    # Define callback for processing captures
    async def process_capture(user_id: str, capture_data: Dict[str, Any]):
        async with get_db() as db:
            await activity_analyzer.process_screen_capture(user_id, capture_data, db)
    
    # Start capture in background
    task = asyncio.create_task(
        screen_service.start_capture_loop(user_id, process_capture)
    )
    active_captures[user_id] = task
    
    return {
        "status": "started",
        "message": "Screen capture started successfully",
        "capture_interval": screen_service.capture_interval
    }


@router.post("/stop")
async def stop_screen_capture(
    current_user: dict = Depends(get_current_user)
):
    """Stop screen capture for the current user"""
    user_id = current_user["user_id"]
    
    if user_id not in active_captures:
        return {"status": "not_running", "message": "No active screen capture"}
    
    # Stop the capture
    screen_service.stop_capture()
    
    # Cancel the task
    task = active_captures.get(user_id)
    if task:
        task.cancel()
    
    # Remove from active captures
    active_captures.pop(user_id, None)
    
    return {
        "status": "stopped",
        "message": "Screen capture stopped successfully"
    }


@router.get("/status")
async def get_capture_status(
    current_user: dict = Depends(get_current_user)
):
    """Get screen capture status for the current user"""
    user_id = current_user["user_id"]
    
    is_active = user_id in active_captures
    
    return {
        "active": is_active,
        "capture_interval": screen_service.capture_interval if is_active else None
    }


@router.post("/capture-once")
async def capture_single_screenshot(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Capture and analyze a single screenshot"""
    user_id = current_user["user_id"]
    
    try:
        # Capture screen
        screenshot = screen_service.capture_screen()
        
        # Analyze
        analysis = await screen_service.analyze_screenshot(screenshot, user_id)
        
        # Process with activity analyzer
        await activity_analyzer.process_screen_capture(user_id, analysis, db)
        
        # Remove sensitive data before returning
        safe_analysis = {
            "timestamp": analysis["timestamp"],
            "activity_type": analysis["activity_type"],
            "detected_applications": analysis["detected_applications"],
            "brightness": analysis["brightness"],
            "ui_elements": analysis["ui_elements"]
        }
        
        return {
            "status": "success",
            "analysis": safe_analysis
        }
        
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to capture screenshot")


@router.get("/activity-summary")
async def get_activity_summary(
    hours: int = 24,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activity summary for the past N hours"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Get summary from screen service
        screen_summary = await screen_service.get_activity_summary(current_user["user_id"], hours)
        
        # Get daily summary from analyzer
        daily_summary = await activity_analyzer.generate_daily_summary(user_id, db)
        
        return {
            "screen_summary": screen_summary,
            "analysis_summary": daily_summary,
            "time_range": {
                "start": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
                "end": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting activity summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get activity summary")


@router.post("/analyze-batch")
async def analyze_activity_batch(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger batch analysis of buffered activities"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        await activity_analyzer.analyze_activity_batch(user_id, db)
        
        return {
            "status": "success",
            "message": "Batch analysis completed"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing batch: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze activity batch")


@router.get("/recommendations")
async def get_activity_recommendations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized recommendations based on screen activity patterns"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Generate daily summary which includes recommendations
        summary = await activity_analyzer.generate_daily_summary(user_id, db)
        
        return {
            "recommendations": summary.get("recommendations", []),
            "productivity_score": summary.get("average_productivity", 0),
            "focus_score": summary.get("average_focus", 0),
            "activity_breakdown": dict(summary.get("activity_breakdown", {}))
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.post("/settings")
async def update_capture_settings(
    settings: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Update screen capture settings"""
    user_id = current_user["user_id"]
    
    # Update capture interval if provided
    if "capture_interval" in settings:
        interval = settings["capture_interval"]
        if 10 <= interval <= 300:  # Between 10 seconds and 5 minutes
            screen_service.capture_interval = interval
        else:
            raise HTTPException(status_code=400, detail="Capture interval must be between 10 and 300 seconds")
    
    # Update analysis interval if provided
    if "analysis_interval" in settings:
        interval = settings["analysis_interval"]
        if 60 <= interval <= 1800:  # Between 1 minute and 30 minutes
            activity_analyzer.analysis_interval = interval
        else:
            raise HTTPException(status_code=400, detail="Analysis interval must be between 60 and 1800 seconds")
    
    return {
        "status": "updated",
        "settings": {
            "capture_interval": screen_service.capture_interval,
            "analysis_interval": activity_analyzer.analysis_interval
        }
    }