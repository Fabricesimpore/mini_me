from fastapi import APIRouter, Depends
from typing import List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
import random

router = APIRouter()

# Schemas
class ModelStatus(BaseModel):
    model_name: str
    status: str  # ready, training, error
    accuracy: float
    last_updated: datetime
    predictions_made: int

class Insight(BaseModel):
    category: str
    title: str
    description: str
    confidence: float
    importance: str  # high, medium, low
    timestamp: datetime

class Prediction(BaseModel):
    type: str
    prediction: str
    confidence: float
    timeframe: str
    factors: List[str]

# Mock ML models status
models = {
    "behavior_predictor": {
        "model_name": "Behavior Pattern Predictor",
        "status": "ready",
        "accuracy": 0.87,
        "last_updated": datetime.utcnow() - timedelta(hours=2),
        "predictions_made": 156
    },
    "sentiment_analyzer": {
        "model_name": "Sentiment Analyzer",
        "status": "ready",
        "accuracy": 0.92,
        "last_updated": datetime.utcnow() - timedelta(days=1),
        "predictions_made": 423
    },
    "recommendation_engine": {
        "model_name": "Personal Recommendation Engine",
        "status": "training",
        "accuracy": 0.79,
        "last_updated": datetime.utcnow() - timedelta(minutes=30),
        "predictions_made": 89
    }
}

@router.get("/models/status", response_model=List[ModelStatus])
async def get_models_status():
    """Get status of all ML models"""
    return [ModelStatus(**model) for model in models.values()]

@router.get("/insights", response_model=List[Insight])
async def get_ml_insights():
    """Get AI-generated insights"""
    insights = [
        {
            "category": "Productivity",
            "title": "Peak Performance Window Detected",
            "description": "Your cognitive performance peaks between 9-11 AM. Schedule important tasks during this window.",
            "confidence": 0.89,
            "importance": "high",
            "timestamp": datetime.utcnow() - timedelta(hours=1)
        },
        {
            "category": "Health",
            "title": "Screen Time Pattern Alert",
            "description": "Your screen time has increased by 23% this week. Consider taking more frequent breaks.",
            "confidence": 0.76,
            "importance": "medium",
            "timestamp": datetime.utcnow() - timedelta(hours=3)
        },
        {
            "category": "Communication",
            "title": "Response Time Optimization",
            "description": "You respond fastest to emails marked as urgent. Consider using filters for better prioritization.",
            "confidence": 0.84,
            "importance": "medium",
            "timestamp": datetime.utcnow() - timedelta(days=1)
        }
    ]
    return [Insight(**insight) for insight in insights]

@router.get("/predictions", response_model=List[Prediction])
async def get_predictions():
    """Get predictive insights"""
    predictions = [
        {
            "type": "energy_level",
            "prediction": "Energy dip expected around 2:30 PM",
            "confidence": 0.82,
            "timeframe": "today",
            "factors": ["Historical patterns", "Current activity level", "Sleep quality"]
        },
        {
            "type": "task_completion",
            "prediction": "High probability of completing current sprint goals",
            "confidence": 0.91,
            "timeframe": "this_week",
            "factors": ["Current velocity", "Task complexity", "Historical performance"]
        },
        {
            "type": "mood",
            "prediction": "Positive mood trajectory for the next 3 days",
            "confidence": 0.73,
            "timeframe": "next_3_days",
            "factors": ["Recent activities", "Social interactions", "Achievement patterns"]
        }
    ]
    return [Prediction(**pred) for pred in predictions]

@router.post("/train/{model_name}")
async def train_model(model_name: str):
    """Trigger model training"""
    if model_name not in models:
        return {"error": "Model not found"}
    
    models[model_name]["status"] = "training"
    return {
        "status": "training_started",
        "model": model_name,
        "estimated_time": "15 minutes"
    }

@router.get("/analysis/text")
async def analyze_text(text: str):
    """Analyze text for sentiment and insights"""
    # Mock analysis
    return {
        "sentiment": {
            "positive": 0.65,
            "neutral": 0.25,
            "negative": 0.10
        },
        "emotions": {
            "joy": 0.45,
            "anticipation": 0.30,
            "trust": 0.25
        },
        "topics": ["work", "productivity", "goals"],
        "summary": "The text expresses optimism about work progress and future goals."
    }

@router.get("/personalization/profile")
async def get_personalization_profile():
    """Get user's personalization profile based on ML analysis"""
    return {
        "personality_traits": {
            "openness": 0.78,
            "conscientiousness": 0.85,
            "extraversion": 0.62,
            "agreeableness": 0.73,
            "neuroticism": 0.35
        },
        "work_style": "Deep Focus",
        "communication_preference": "Asynchronous",
        "learning_style": "Visual",
        "decision_making": "Data-driven",
        "stress_triggers": ["Tight deadlines", "Unclear requirements"],
        "motivators": ["Problem solving", "Learning new technologies", "Team collaboration"]
    }