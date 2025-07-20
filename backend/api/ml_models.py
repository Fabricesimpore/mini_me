from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.auth import get_current_user
from services.ml_service import MLService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize ML service
ml_service = MLService()


@router.post("/train/behavioral")
async def train_behavioral_model(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Train behavioral pattern recognition model"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Run training in background for large datasets
        result = await ml_service.train_behavioral_model(db, user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Schedule periodic retraining
        background_tasks.add_task(ml_service.schedule_model_retraining, db, user_id)
        
        return {
            "status": "success",
            "training_result": result
        }
        
    except Exception as e:
        logger.error(f"Error training behavioral model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/communication")
async def train_communication_model(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Train communication style model"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        result = await ml_service.train_communication_model(db, user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "training_result": result
        }
        
    except Exception as e:
        logger.error(f"Error training communication model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/current-behavior")
async def analyze_current_behavior(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze current behavioral pattern"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        analysis = await ml_service.analyze_current_behavior(db, user_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing behavior: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/communication")
async def analyze_communication(
    messages: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze communication patterns from messages"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        analysis = await ml_service.analyze_communication_batch(db, user_id, messages)
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing communication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_behavioral_insights(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive behavioral insights"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        insights = await ml_service.get_behavioral_insights(db, user_id)
        
        if "error" in insights:
            raise HTTPException(status_code=400, detail=insights["error"])
        
        return {
            "status": "success",
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/activity")
async def predict_activity_pattern(
    recent_behaviors: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Predict activity pattern from recent behaviors"""
    user_id = current_user["user_id"]
    
    try:
        if len(recent_behaviors) < 5:
            raise HTTPException(
                status_code=400, 
                detail="Need at least 5 recent behaviors for prediction"
            )
        
        # Use the behavioral pattern trainer directly
        prediction = ml_service.behavioral_trainer.predict_pattern(recent_behaviors)
        
        if "error" in prediction:
            raise HTTPException(status_code=400, detail=prediction["error"])
        
        return {
            "status": "success",
            "prediction": prediction
        }
        
    except Exception as e:
        logger.error(f"Error predicting activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest/communication")
async def get_communication_suggestions(
    context: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get communication style suggestions based on user profile"""
    user_id = current_user["user_id"]
    
    try:
        suggestions = ml_service.communication_analyzer.generate_message_suggestion(
            user_id, context
        )
        
        if "error" in suggestions:
            raise HTTPException(status_code=400, detail=suggestions["error"])
        
        return {
            "status": "success",
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status")
async def get_model_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get status of trained models for the user"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        # Check for existing models
        behavioral_model_exists = ml_service.behavioral_trainer.model is not None
        
        # Check for communication profile
        from pathlib import Path
        comm_profile_path = Path(ml_service.communication_analyzer.model_path) / f'communication_profile_{user_id}.pkl'
        communication_profile_exists = comm_profile_path.exists()
        
        # Get last training info from memories
        from services.memory_service import MemoryService
        memory_service = MemoryService()
        
        training_memories = await memory_service.search_memories(
            db,
            user_id=user_id,
            source_filter="ml_training",
            limit=10
        )
        
        last_trainings = {}
        for memory in training_memories:
            model_type = memory.get('metadata', {}).get('model_type')
            if model_type and model_type not in last_trainings:
                last_trainings[model_type] = {
                    'timestamp': memory.get('timestamp'),
                    'result': memory.get('metadata', {}).get('training_result', {})
                }
        
        return {
            "models": {
                "behavioral_pattern": {
                    "trained": behavioral_model_exists,
                    "last_training": last_trainings.get('behavioral_pattern')
                },
                "communication_style": {
                    "trained": communication_profile_exists,
                    "last_training": last_trainings.get('communication_style')
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking model status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/all")
async def train_all_models(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Train all available models for the user"""
    user_id = uuid.UUID(current_user["user_id"])
    
    try:
        results = {}
        
        # Train behavioral model
        behavioral_result = await ml_service.train_behavioral_model(db, user_id)
        results["behavioral_pattern"] = behavioral_result
        
        # Train communication model
        comm_result = await ml_service.train_communication_model(db, user_id)
        results["communication_style"] = comm_result
        
        # Schedule periodic retraining
        background_tasks.add_task(ml_service.schedule_model_retraining, db, user_id)
        
        # Check for errors
        errors = {k: v for k, v in results.items() if "error" in v}
        
        if errors:
            return {
                "status": "partial_success",
                "results": results,
                "errors": errors
            }
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error training all models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))