from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.auth import get_current_user
from collectors.screen_collector import ScreenObserver
from collectors.communication_collector import CommunicationAnalyzer

router = APIRouter()

# Initialize collectors
screen_observer = ScreenObserver()
communication_analyzer = CommunicationAnalyzer()


@router.post("/start-observation")
async def start_observation(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start observing user behavior"""
    user_id = current_user["user_id"]
    
    # Start screen observation
    await screen_observer.start_observation(user_id)
    
    return {
        "status": "observation_started",
        "user_id": user_id,
        "started_at": datetime.utcnow()
    }


@router.post("/stop-observation")
async def stop_observation(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop observing user behavior"""
    user_id = current_user["user_id"]
    
    # Stop observation
    screen_observer.stop_observation()
    
    return {
        "status": "observation_stopped",
        "user_id": user_id,
        "stopped_at": datetime.utcnow()
    }


@router.post("/analyze-communication")
async def analyze_communication(
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze communication patterns"""
    user_id = current_user["user_id"]
    
    # Analyze the provided communication data
    analysis = await communication_analyzer.analyze_communication(data)
    
    # TODO: Store analysis in database
    
    return {
        "user_id": user_id,
        "analysis": analysis,
        "analyzed_at": datetime.utcnow()
    }


@router.get("/patterns")
async def get_behavioral_patterns(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get learned behavioral patterns for user"""
    user_id = current_user["user_id"]
    
    # TODO: Fetch from database
    patterns = {
        "navigation": {
            "most_visited_sites": ["gmail.com", "github.com", "stackoverflow.com"],
            "avg_time_per_site": {"gmail.com": 15, "github.com": 45, "stackoverflow.com": 10},
            "peak_activity_hours": [9, 10, 14, 15, 16]
        },
        "communication": {
            "email_response_time": 2.5,  # hours
            "preferred_greeting": "Hi",
            "preferred_closing": "Best regards",
            "avg_message_length": 150
        },
        "decision_making": {
            "avg_decision_time": 5.2,  # minutes
            "comparison_sites_used": 3,
            "price_sensitivity": "medium"
        }
    }
    
    return {
        "user_id": user_id,
        "patterns": patterns,
        "last_updated": datetime.utcnow()
    }


@router.post("/record-decision")
async def record_decision(
    decision_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Record a decision made by the user"""
    user_id = current_user["user_id"]
    
    # TODO: Process and store decision data
    
    return {
        "status": "decision_recorded",
        "user_id": user_id,
        "decision_id": "temp-decision-id",
        "recorded_at": datetime.utcnow()
    }