from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.auth import get_current_user
from services.recommendation_engine import RecommendationEngine

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()


@router.get("/general")
async def get_general_recommendations(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get general recommendations based on user patterns"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Build context if category specified
        context = {}
        if category:
            if category not in ['productivity', 'communication', 'wellness', 'learning', 'social']:
                raise HTTPException(status_code=400, detail="Invalid category")
            context['focus_category'] = category
        
        # Generate recommendations
        result = await recommendation_engine.generate_recommendations(db, user_id, context)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decision-support")
async def get_decision_support(
    decision_context: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get decision support for a specific decision"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Validate decision context
        if not decision_context.get('decision_type'):
            raise HTTPException(
                status_code=400, 
                detail="decision_type is required (e.g., career, financial, purchase, personal)"
            )
        
        # Get decision support
        result = await recommendation_engine.get_decision_support(
            db, user_id, decision_context
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "decision_support": result
        }
        
    except Exception as e:
        logger.error(f"Error getting decision support: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/productivity")
async def get_productivity_recommendations(
    timeframe: str = "today",
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get productivity-specific recommendations"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        context = {
            'focus_category': 'productivity',
            'timeframe': timeframe
        }
        
        result = await recommendation_engine.generate_recommendations(db, user_id, context)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Extract productivity recommendations
        productivity_recs = result.get('recommendations', {}).get('productivity', [])
        
        return {
            "status": "success",
            "recommendations": productivity_recs,
            "timeframe": timeframe,
            "confidence_score": result.get('confidence_score', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting productivity recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communication")
async def get_communication_recommendations(
    context_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get communication-specific recommendations"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        context = {
            'focus_category': 'communication'
        }
        
        if context_type:
            context['communication_context'] = context_type  # email, meeting, chat, etc.
        
        result = await recommendation_engine.generate_recommendations(db, user_id, context)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Extract communication recommendations
        comm_recs = result.get('recommendations', {}).get('communication', [])
        
        return {
            "status": "success",
            "recommendations": comm_recs,
            "context_type": context_type,
            "confidence_score": result.get('confidence_score', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting communication recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wellness")
async def get_wellness_recommendations(
    focus_area: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get wellness and work-life balance recommendations"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        context = {
            'focus_category': 'wellness'
        }
        
        if focus_area:
            if focus_area not in ['stress', 'energy', 'balance', 'habits']:
                raise HTTPException(status_code=400, detail="Invalid focus area")
            context['wellness_focus'] = focus_area
        
        result = await recommendation_engine.generate_recommendations(db, user_id, context)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Extract wellness recommendations
        wellness_recs = result.get('recommendations', {}).get('wellness', [])
        
        return {
            "status": "success",
            "recommendations": wellness_recs,
            "focus_area": focus_area,
            "confidence_score": result.get('confidence_score', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting wellness recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-decision")
async def get_quick_decision_help(
    decision_info: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get quick decision help for time-sensitive decisions"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Add time pressure context
        decision_context = {
            **decision_info,
            'time_pressure': True,
            'quick_decision': True
        }
        
        result = await recommendation_engine.get_decision_support(
            db, user_id, decision_context
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Extract key points for quick decision
        quick_framework = {
            'immediate_steps': result.get('decision_framework', {}).get('steps', [])[:3],
            'key_factors': list(result.get('confidence_factors', {}).get('strengths', []))[:2],
            'quick_tools': ['Pros/Cons list', '10-10-10 rule', 'Gut check'],
            'time_limit': '30 minutes recommended'
        }
        
        return {
            "status": "success",
            "quick_framework": quick_framework,
            "top_recommendation": result.get('recommendations', [{}])[0] if result.get('recommendations') else None
        }
        
    except Exception as e:
        logger.error(f"Error getting quick decision help: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily")
async def get_daily_recommendations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get daily personalized recommendations"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Generate comprehensive daily recommendations
        context = {
            'timeframe': 'today',
            'comprehensive': True
        }
        
        result = await recommendation_engine.generate_recommendations(db, user_id, context)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Format for daily digest
        all_recommendations = result.get('recommendations', {})
        
        # Flatten and prioritize
        daily_recs = []
        for category, recs in all_recommendations.items():
            if isinstance(recs, list):
                for rec in recs:
                    rec['category'] = category
                    daily_recs.append(rec)
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        daily_recs.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
        
        # Take top 5
        top_daily = daily_recs[:5]
        
        return {
            "status": "success",
            "daily_recommendations": top_daily,
            "total_recommendations": len(daily_recs),
            "generated_at": result.get('generated_at'),
            "confidence_score": result.get('confidence_score', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting daily recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_recommendation_feedback(
    feedback: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback on recommendations"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Validate feedback
        if 'recommendation_id' not in feedback:
            raise HTTPException(status_code=400, detail="recommendation_id is required")
        
        if 'rating' not in feedback:
            raise HTTPException(status_code=400, detail="rating is required (1-5)")
        
        rating = feedback['rating']
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=400, detail="rating must be between 1 and 5")
        
        # Store feedback as memory
        from services.memory_service import MemoryService
        memory_service = MemoryService()
        
        await memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="episodic",
            content=f"Rated recommendation {feedback['recommendation_id']}: {rating}/5",
            source="recommendation_feedback",
            metadata={
                "recommendation_id": feedback['recommendation_id'],
                "rating": rating,
                "helpful": rating >= 4,
                "comments": feedback.get('comments', ''),
                "applied": feedback.get('applied', False)
            }
        )
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_recommendation_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get history of past recommendations"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Get recommendation memories
        from services.memory_service import MemoryService
        memory_service = MemoryService()
        
        recommendation_memories = await memory_service.search_memories(
            db,
            user_id=user_id,
            source_filter="recommendation_engine",
            limit=limit
        )
        
        # Format history
        history = []
        for memory in recommendation_memories:
            metadata = memory.get('metadata', {})
            recommendations = metadata.get('recommendations', {})
            
            # Count recommendations by category
            category_counts = {}
            for category, recs in recommendations.items():
                if isinstance(recs, list):
                    category_counts[category] = len(recs)
            
            history.append({
                'id': memory.get('id'),
                'timestamp': memory.get('timestamp'),
                'summary': memory.get('content'),
                'category_counts': category_counts,
                'high_priority_count': metadata.get('high_priority_count', 0)
            })
        
        return {
            "status": "success",
            "history": history,
            "total_items": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))