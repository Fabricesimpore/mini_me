from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import uuid

from core.database import get_db
from api.auth import get_current_user
from app.services.cognitive_profile_service import CognitiveProfileService

router = APIRouter()
profile_service = CognitiveProfileService()

@router.post("/analyze")
async def analyze_profile(
    force_full_analysis: bool = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze user's cognitive profile based on their memories and interactions"""
    user_id = current_user["user_id"]
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    result = await profile_service.analyze_user_profile(
        db=db,
        user_id=user_uuid,
        force_full_analysis=force_full_analysis
    )
    
    return result

@router.get("/")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the user's current cognitive profile"""
    user_id = current_user["user_id"]
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    profile = await profile_service.get_or_create_profile(db, user_uuid)
    
    if profile.analysis_count == 0:
        return {
            "status": "not_analyzed",
            "message": "Profile not yet analyzed. Run analysis first.",
            "profile": None
        }
    
    return {
        "status": "success",
        "profile": profile_service._serialize_profile(profile)
    }

@router.get("/insights")
async def get_profile_insights(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized insights based on cognitive profile"""
    user_id = current_user["user_id"]
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    insights = await profile_service.get_profile_insights(db, user_uuid)
    
    return insights

@router.get("/personality-report")
async def get_personality_report(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a detailed personality report"""
    user_id = current_user["user_id"]
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    profile = await profile_service.get_or_create_profile(db, user_uuid)
    
    if profile.analysis_count == 0:
        raise HTTPException(status_code=404, detail="Profile not yet analyzed")
    
    # Generate detailed report
    report = {
        "personality_overview": {
            "openness": {
                "score": profile.openness,
                "level": "high" if profile.openness > 0.7 else "moderate" if profile.openness > 0.3 else "low",
                "description": _get_trait_description("openness", profile.openness)
            },
            "conscientiousness": {
                "score": profile.conscientiousness,
                "level": "high" if profile.conscientiousness > 0.7 else "moderate" if profile.conscientiousness > 0.3 else "low",
                "description": _get_trait_description("conscientiousness", profile.conscientiousness)
            },
            "extraversion": {
                "score": profile.extraversion,
                "level": "high" if profile.extraversion > 0.7 else "moderate" if profile.extraversion > 0.3 else "low",
                "description": _get_trait_description("extraversion", profile.extraversion)
            },
            "agreeableness": {
                "score": profile.agreeableness,
                "level": "high" if profile.agreeableness > 0.7 else "moderate" if profile.agreeableness > 0.3 else "low",
                "description": _get_trait_description("agreeableness", profile.agreeableness)
            },
            "neuroticism": {
                "score": profile.neuroticism,
                "level": "high" if profile.neuroticism > 0.7 else "moderate" if profile.neuroticism > 0.3 else "low",
                "description": _get_trait_description("neuroticism", profile.neuroticism)
            }
        },
        "work_style": {
            "collaboration_preference": profile.work_style,
            "peak_performance": profile.peak_productivity_hours,
            "preferred_tasks": profile.preferred_task_types,
            "decision_style": "analytical" if profile.analytical_vs_intuitive > 0.5 else "intuitive",
            "risk_profile": "risk-seeking" if profile.risk_tolerance > 0.7 else "balanced" if profile.risk_tolerance > 0.3 else "risk-averse"
        },
        "communication_profile": {
            "formality": "formal" if profile.communication_formality > 0.7 else "balanced" if profile.communication_formality > 0.3 else "informal",
            "verbosity": "verbose" if profile.communication_verbosity > 0.7 else "balanced" if profile.communication_verbosity > 0.3 else "concise",
            "channels": profile.preferred_communication_channels
        },
        "emotional_intelligence": {
            "stability": profile.emotional_stability,
            "stress_management": {
                "triggers": profile.stress_triggers,
                "coping_strategies": profile.coping_mechanisms
            }
        },
        "social_dynamics": {
            "energy_type": "extrovert" if profile.social_energy > 0.5 else "introvert",
            "relationship_style": "deep connections" if profile.relationship_depth > 0.5 else "broad network"
        },
        "interests_and_expertise": {
            "top_interests": dict(list(profile.interest_categories.items())[:5]) if profile.interest_categories else {},
            "expertise_areas": profile.expertise_areas
        },
        "profile_metadata": {
            "confidence": profile.profile_confidence,
            "data_points": profile.data_points,
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else None
        }
    }
    
    return report

def _get_trait_description(trait: str, score: float) -> str:
    """Generate description for personality trait based on score"""
    descriptions = {
        "openness": {
            "high": "You are highly creative, curious, and open to new experiences. You enjoy exploring new ideas and unconventional approaches.",
            "moderate": "You balance openness to new experiences with appreciation for familiar routines.",
            "low": "You prefer familiar routines and conventional approaches. You value stability and predictability."
        },
        "conscientiousness": {
            "high": "You are highly organized, reliable, and goal-oriented. You excel at planning and following through on commitments.",
            "moderate": "You balance organization with flexibility, adapting your approach to the situation.",
            "low": "You prefer spontaneity and flexibility over rigid structure. You adapt easily to changing circumstances."
        },
        "extraversion": {
            "high": "You are energized by social interactions and external stimulation. You thrive in group settings and enjoy being the center of attention.",
            "moderate": "You enjoy both social time and solitude, adapting to different social situations comfortably.",
            "low": "You prefer quiet environments and small group interactions. You recharge through solitude and reflection."
        },
        "agreeableness": {
            "high": "You are highly cooperative, trusting, and empathetic. You prioritize harmony and helping others.",
            "moderate": "You balance cooperation with assertiveness, standing up for yourself when needed.",
            "low": "You are direct, competitive, and skeptical. You prioritize truth and results over harmony."
        },
        "neuroticism": {
            "high": "You experience emotions intensely and may be prone to stress and anxiety. You're highly sensitive to your environment.",
            "moderate": "You experience a normal range of emotions and generally cope well with stress.",
            "low": "You are emotionally stable and resilient. You remain calm under pressure and recover quickly from setbacks."
        }
    }
    
    level = "high" if score > 0.7 else "moderate" if score > 0.3 else "low"
    return descriptions.get(trait, {}).get(level, "No description available")

@router.post("/update-preference")
async def update_preference(
    preference_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually update a specific preference in the profile"""
    user_id = current_user["user_id"]
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    profile = await profile_service.get_or_create_profile(db, user_uuid)
    
    # Validate and update preference
    allowed_preferences = [
        "preferred_communication_channels",
        "peak_productivity_hours",
        "preferred_task_types",
        "stress_triggers",
        "coping_mechanisms"
    ]
    
    preference_key = preference_data.get("key")
    preference_value = preference_data.get("value")
    
    if preference_key not in allowed_preferences:
        raise HTTPException(status_code=400, detail=f"Invalid preference key: {preference_key}")
    
    setattr(profile, preference_key, preference_value)
    await db.commit()
    await db.refresh(profile)
    
    return {
        "status": "success",
        "updated": {preference_key: preference_value},
        "profile": profile_service._serialize_profile(profile)
    }