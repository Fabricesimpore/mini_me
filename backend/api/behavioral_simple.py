from fastapi import APIRouter, Depends
from typing import List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
import random

router = APIRouter()

# Schemas
class BehavioralPattern(BaseModel):
    pattern_type: str
    description: str
    frequency: float
    confidence: float
    last_observed: datetime

class ActivitySummary(BaseModel):
    activity_type: str
    duration_minutes: int
    count: int
    productivity_score: float

class MoodEntry(BaseModel):
    mood: str
    energy_level: int
    notes: str
    timestamp: datetime

# Mock data
def generate_mock_patterns():
    patterns = [
        {
            "pattern_type": "work_schedule",
            "description": "Most productive between 9 AM - 12 PM",
            "frequency": 0.85,
            "confidence": 0.92,
            "last_observed": datetime.utcnow() - timedelta(hours=2)
        },
        {
            "pattern_type": "break_pattern",
            "description": "Takes 5-minute breaks every 45 minutes",
            "frequency": 0.72,
            "confidence": 0.88,
            "last_observed": datetime.utcnow() - timedelta(hours=1)
        },
        {
            "pattern_type": "communication",
            "description": "Prefers email for formal communication",
            "frequency": 0.90,
            "confidence": 0.95,
            "last_observed": datetime.utcnow() - timedelta(days=1)
        }
    ]
    return patterns

@router.get("/patterns", response_model=List[BehavioralPattern])
async def get_behavioral_patterns():
    """Get identified behavioral patterns"""
    return [BehavioralPattern(**p) for p in generate_mock_patterns()]

@router.get("/activity-summary", response_model=List[ActivitySummary])
async def get_activity_summary(days: int = 7):
    """Get activity summary for the past N days"""
    activities = [
        ActivitySummary(
            activity_type="Coding",
            duration_minutes=240,
            count=12,
            productivity_score=0.85
        ),
        ActivitySummary(
            activity_type="Meetings",
            duration_minutes=90,
            count=3,
            productivity_score=0.70
        ),
        ActivitySummary(
            activity_type="Email",
            duration_minutes=60,
            count=25,
            productivity_score=0.65
        ),
        ActivitySummary(
            activity_type="Research",
            duration_minutes=120,
            count=5,
            productivity_score=0.90
        )
    ]
    return activities

@router.post("/mood", response_model=MoodEntry)
async def log_mood(mood: str, energy_level: int, notes: str = ""):
    """Log current mood and energy level"""
    entry = MoodEntry(
        mood=mood,
        energy_level=energy_level,
        notes=notes,
        timestamp=datetime.utcnow()
    )
    return entry

@router.get("/productivity-score")
async def get_productivity_score():
    """Get current productivity score and trends"""
    return {
        "current_score": 0.78,
        "trend": "increasing",
        "factors": {
            "focus_time": 0.85,
            "task_completion": 0.72,
            "break_consistency": 0.80,
            "energy_management": 0.75
        },
        "recommendations": [
            "Consider taking a short break to maintain focus",
            "Your morning productivity is excellent - leverage this time for complex tasks",
            "Try the Pomodoro technique for afternoon sessions"
        ]
    }

@router.get("/habits")
async def get_habits():
    """Get tracked habits and their completion rates"""
    return {
        "habits": [
            {
                "name": "Morning meditation",
                "streak": 12,
                "completion_rate": 0.85,
                "impact_score": 0.90
            },
            {
                "name": "Daily coding practice",
                "streak": 45,
                "completion_rate": 0.95,
                "impact_score": 0.88
            },
            {
                "name": "Evening walk",
                "streak": 7,
                "completion_rate": 0.70,
                "impact_score": 0.82
            }
        ],
        "insights": "Your consistency with daily coding practice is exceptional!"
    }