from fastapi import APIRouter
from typing import List, Dict, Optional, Any
from datetime import datetime, time
from pydantic import BaseModel

router = APIRouter()

# Schemas
class Recommendation(BaseModel):
    id: str
    category: str
    title: str
    description: str
    priority: str  # high, medium, low
    impact_score: float
    action_items: List[str]
    reasoning: str
    expires_at: Optional[datetime] = None

class DailyPlan(BaseModel):
    date: datetime
    energy_forecast: Dict[str, float]  # hour -> energy level
    recommended_schedule: List[Dict[str, Any]]
    focus_blocks: List[Dict[str, Any]]
    break_suggestions: List[Dict[str, Any]]

@router.get("/daily", response_model=List[Recommendation])
async def get_daily_recommendations():
    """Get personalized daily recommendations"""
    recommendations = [
        {
            "id": "rec_1",
            "category": "productivity",
            "title": "Start with Deep Work Session",
            "description": "Your cognitive performance is highest in the morning. Tackle your most challenging task first.",
            "priority": "high",
            "impact_score": 0.92,
            "action_items": [
                "Review your task list and identify the most complex item",
                "Set a 90-minute focus timer",
                "Turn off all notifications"
            ],
            "reasoning": "Based on your past performance data, you complete complex tasks 40% faster in morning sessions."
        },
        {
            "id": "rec_2",
            "category": "health",
            "title": "Hydration Reminder Setup",
            "description": "You tend to forget drinking water during focused work sessions.",
            "priority": "medium",
            "impact_score": 0.75,
            "action_items": [
                "Set hourly water reminders",
                "Keep a water bottle at your desk",
                "Track daily water intake"
            ],
            "reasoning": "Your productivity drops by 15% when dehydrated based on activity patterns."
        },
        {
            "id": "rec_3",
            "category": "learning",
            "title": "Skill Development: Advanced Python",
            "description": "Based on your recent searches and projects, advancing your Python skills would be beneficial.",
            "priority": "medium",
            "impact_score": 0.83,
            "action_items": [
                "Dedicate 30 minutes daily to Python advanced topics",
                "Focus on async programming patterns",
                "Build a small project using new concepts"
            ],
            "reasoning": "You've shown interest in FastAPI and async patterns. Deepening this knowledge aligns with your goals."
        }
    ]
    
    return [Recommendation(**rec) for rec in recommendations]

@router.get("/schedule")
async def get_optimized_schedule():
    """Get an optimized daily schedule based on patterns"""
    return {
        "date": datetime.utcnow().date(),
        "energy_forecast": {
            "09:00": 0.95,
            "10:00": 0.92,
            "11:00": 0.88,
            "12:00": 0.75,
            "13:00": 0.65,
            "14:00": 0.70,
            "15:00": 0.78,
            "16:00": 0.73,
            "17:00": 0.68
        },
        "recommended_schedule": [
            {
                "time": "09:00 - 10:30",
                "activity": "Deep Work",
                "task": "Complex problem solving",
                "energy_required": "high"
            },
            {
                "time": "10:30 - 10:45",
                "activity": "Break",
                "task": "Walk and hydrate",
                "energy_required": "low"
            },
            {
                "time": "10:45 - 12:00",
                "activity": "Focused Work",
                "task": "Code implementation",
                "energy_required": "medium-high"
            },
            {
                "time": "12:00 - 13:00",
                "activity": "Lunch Break",
                "task": "Eat and recharge",
                "energy_required": "low"
            },
            {
                "time": "13:00 - 14:00",
                "activity": "Meetings/Communication",
                "task": "Team sync and emails",
                "energy_required": "medium"
            },
            {
                "time": "14:00 - 15:30",
                "activity": "Creative Work",
                "task": "Design and planning",
                "energy_required": "medium"
            },
            {
                "time": "15:30 - 17:00",
                "activity": "Learning Time",
                "task": "Skill development",
                "energy_required": "medium"
            }
        ]
    }

@router.get("/habits")
async def get_habit_recommendations():
    """Get recommendations for building better habits"""
    return {
        "current_habits": {
            "positive": [
                "Consistent morning start time",
                "Regular code commits",
                "Daily learning sessions"
            ],
            "needs_improvement": [
                "Irregular break schedule",
                "Late night screen time",
                "Inconsistent exercise"
            ]
        },
        "recommended_habits": [
            {
                "habit": "Pomodoro Technique",
                "description": "25-minute focused sessions with 5-minute breaks",
                "expected_impact": "20% productivity increase",
                "implementation_tips": [
                    "Start with 3 pomodoros per day",
                    "Gradually increase to 6-8",
                    "Use a physical timer"
                ]
            },
            {
                "habit": "Evening Shutdown Ritual",
                "description": "Structured end to work day",
                "expected_impact": "Better work-life balance and sleep",
                "implementation_tips": [
                    "Set a fixed shutdown time",
                    "Review tomorrow's priorities",
                    "Close all work applications"
                ]
            }
        ]
    }

@router.get("/wellness")
async def get_wellness_recommendations():
    """Get wellness and self-care recommendations"""
    return {
        "stress_level": "moderate",
        "recommendations": [
            {
                "area": "Mental Health",
                "suggestions": [
                    "5-minute meditation after lunch",
                    "Gratitude journaling before bed",
                    "Limit news consumption to 15 minutes"
                ]
            },
            {
                "area": "Physical Health",
                "suggestions": [
                    "Stand and stretch every hour",
                    "Take walking meetings when possible",
                    "Do desk exercises during breaks"
                ]
            },
            {
                "area": "Social Connection",
                "suggestions": [
                    "Schedule weekly coffee with a colleague",
                    "Join a professional community",
                    "Participate in team activities"
                ]
            }
        ],
        "personalized_tip": "Your stress levels tend to rise on Thursdays. Plan lighter workloads and more breaks on this day."
    }

@router.post("/feedback/{recommendation_id}")
async def provide_recommendation_feedback(
    recommendation_id: str,
    helpful: bool,
    implemented: bool
):
    """Provide feedback on recommendations"""
    return {
        "status": "feedback_recorded",
        "message": "Thank you for your feedback. This helps improve future recommendations.",
        "recommendation_id": recommendation_id,
        "impact": "Your feedback will be used to personalize future suggestions."
    }