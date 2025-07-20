import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ml.behavioral_pattern_model import BehavioralPatternTrainer
from ml.communication_style_model import CommunicationStyleAnalyzer
from app.services.memory_service import MemoryService
from app.services.cognitive_profile_service import CognitiveProfileService
from core.models.user import User
from core.models.behavioral import BehavioralData

logger = logging.getLogger(__name__)


class MLService:
    """Service for training and using ML models"""
    
    def __init__(self):
        self.behavioral_trainer = BehavioralPatternTrainer()
        self.communication_analyzer = CommunicationStyleAnalyzer()
        self.memory_service = MemoryService()
        self.cognitive_service = CognitiveProfileService()
        
    async def train_behavioral_model(self, db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Train behavioral pattern model for a user"""
        try:
            # Fetch behavioral data
            result = await db.execute(
                select(BehavioralData)
                .where(BehavioralData.user_id == user_id)
                .order_by(BehavioralData.timestamp.desc())
                .limit(10000)  # Last 10k behaviors
            )
            behaviors = result.scalars().all()
            
            if len(behaviors) < 100:
                return {
                    "error": "Insufficient behavioral data",
                    "required": 100,
                    "current": len(behaviors)
                }
            
            # Convert to format expected by trainer
            behavior_dicts = []
            for behavior in behaviors:
                behavior_dicts.append({
                    'timestamp': behavior.timestamp,
                    'type': behavior.behavior_type,
                    'data': behavior.data or {},
                    'source': behavior.source
                })
            
            # Train model
            logger.info(f"Training behavioral model for user {user_id}")
            training_result = self.behavioral_trainer.train_model(behavior_dicts)
            
            # Store training result as memory
            await self.memory_service.store_memory(
                db,
                user_id=user_id,
                memory_type="procedural",
                content=f"Trained behavioral pattern model with {training_result.get('training_samples', 0)} samples",
                source="ml_training",
                metadata={
                    "model_type": "behavioral_pattern",
                    "training_result": training_result
                }
            )
            
            return training_result
            
        except Exception as e:
            logger.error(f"Error training behavioral model: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_current_behavior(self, db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Analyze current behavioral pattern"""
        try:
            # Get recent behaviors (last hour)
            since = datetime.utcnow() - timedelta(hours=1)
            result = await db.execute(
                select(BehavioralData)
                .where(
                    (BehavioralData.user_id == user_id) &
                    (BehavioralData.timestamp >= since)
                )
                .order_by(BehavioralData.timestamp.desc())
            )
            recent_behaviors = result.scalars().all()
            
            if len(recent_behaviors) < 5:
                return {
                    "error": "Insufficient recent behavioral data",
                    "message": "Need at least 5 recent behaviors for analysis"
                }
            
            # Convert to format expected by model
            behavior_dicts = []
            for behavior in recent_behaviors:
                behavior_dicts.append({
                    'timestamp': behavior.timestamp,
                    'type': behavior.behavior_type,
                    'data': behavior.data or {},
                    'source': behavior.source
                })
            
            # Predict pattern
            prediction = self.behavioral_trainer.predict_pattern(behavior_dicts)
            
            # Store insight as memory if high confidence
            if prediction.get('confidence', 0) > 0.7:
                await self.memory_service.store_memory(
                    db,
                    user_id=user_id,
                    memory_type="semantic",
                    content=f"Current activity pattern: {prediction['primary_pattern']}",
                    source="behavioral_analysis",
                    metadata={
                        "pattern": prediction['primary_pattern'],
                        "confidence": prediction['confidence'],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                # Update cognitive profile based on pattern
                await self._update_profile_from_pattern(db, user_id, prediction['primary_pattern'])
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error analyzing behavior: {str(e)}")
            return {"error": str(e)}
    
    async def train_communication_model(self, db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Train communication style model for a user"""
        try:
            # Get user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return {"error": "User not found"}
            
            # Collect communication data from various sources
            messages = []
            
            # Get Gmail data if connected
            if user.integrations_data and user.integrations_data.get('gmail', {}).get('connected'):
                # In real implementation, fetch from Gmail API
                # For now, get from memories
                gmail_memories = await self.memory_service.search_memories(
                    db,
                    user_id=user_id,
                    source_filter="gmail_analysis",
                    limit=1000
                )
                
                for memory in gmail_memories:
                    metadata = memory.get('metadata', {})
                    if 'email_samples' in metadata:
                        messages.extend(metadata['email_samples'])
            
            # Get chat messages
            chat_memories = await self.memory_service.search_memories(
                db,
                user_id=user_id,
                memory_type="episodic",
                limit=500
            )
            
            for memory in chat_memories:
                if memory.get('source') == 'chat':
                    messages.append({
                        'content': memory.get('content', ''),
                        'timestamp': memory.get('timestamp'),
                        'type': 'chat'
                    })
            
            if len(messages) < 20:
                return {
                    "error": "Insufficient communication data",
                    "required": 20,
                    "current": len(messages)
                }
            
            # Train model
            logger.info(f"Training communication model for user {user_id}")
            training_result = self.communication_analyzer.train_personalized_model(
                messages, str(user_id)
            )
            
            # Store result as memory
            if training_result.get('status') == 'success':
                await self.memory_service.store_memory(
                    db,
                    user_id=user_id,
                    memory_type="semantic",
                    content=f"Communication style profile: {training_result['profile']['primary_style']}",
                    source="ml_training",
                    metadata={
                        "model_type": "communication_style",
                        "profile": training_result['profile']
                    }
                )
            
            return training_result
            
        except Exception as e:
            logger.error(f"Error training communication model: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_communication_batch(self, db: AsyncSession, user_id: uuid.UUID, 
                                        messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a batch of communications"""
        try:
            # Analyze messages
            analysis = self.communication_analyzer.analyze_communication_batch(messages)
            
            # Store insights
            if 'style_profile' in analysis:
                profile = analysis['style_profile']
                await self.memory_service.store_memory(
                    db,
                    user_id=user_id,
                    memory_type="semantic",
                    content=f"Communication analysis: {profile['primary_style']} style, {profile['formality_level']} formality",
                    source="communication_analysis",
                    metadata={
                        "analysis": analysis,
                        "message_count": len(messages)
                    }
                )
                
                # Update cognitive profile
                await self._update_profile_from_communication(db, user_id, profile)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing communications: {str(e)}")
            return {"error": str(e)}
    
    async def get_behavioral_insights(self, db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get comprehensive behavioral insights for a user"""
        try:
            insights = {
                "behavioral_patterns": [],
                "communication_style": None,
                "productivity_trends": [],
                "recommendations": []
            }
            
            # Get recent behavioral analysis memories
            behavioral_memories = await self.memory_service.search_memories(
                db,
                user_id=user_id,
                source_filter="behavioral_analysis",
                limit=50
            )
            
            # Extract patterns
            pattern_counts = {}
            for memory in behavioral_memories:
                pattern = memory.get('metadata', {}).get('pattern')
                if pattern:
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Sort patterns by frequency
            sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
            insights["behavioral_patterns"] = [
                {"pattern": pattern, "frequency": count}
                for pattern, count in sorted_patterns[:5]
            ]
            
            # Get communication style
            comm_memories = await self.memory_service.search_memories(
                db,
                user_id=user_id,
                source_filter="communication_analysis",
                limit=1
            )
            
            if comm_memories:
                latest_comm = comm_memories[0]
                insights["communication_style"] = latest_comm.get('metadata', {}).get('analysis', {}).get('style_profile')
            
            # Generate recommendations
            insights["recommendations"] = await self._generate_ml_recommendations(
                db, user_id, insights
            )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting behavioral insights: {str(e)}")
            return {"error": str(e)}
    
    async def _update_profile_from_pattern(self, db: AsyncSession, user_id: uuid.UUID, pattern: str):
        """Update cognitive profile based on behavioral pattern"""
        profile_updates = {}
        
        # Map patterns to personality traits
        pattern_trait_map = {
            "productive_flow": {"conscientiousness": 0.8, "openness": 0.6},
            "deep_focus": {"conscientiousness": 0.9, "neuroticism": 0.3},
            "multitasking": {"openness": 0.8, "conscientiousness": 0.5},
            "communication_heavy": {"extraversion": 0.8, "agreeableness": 0.7},
            "creative_work": {"openness": 0.9, "conscientiousness": 0.6},
            "distracted_browsing": {"conscientiousness": 0.3, "neuroticism": 0.6}
        }
        
        if pattern in pattern_trait_map:
            profile_updates = pattern_trait_map[pattern]
            await self.cognitive_service.update_profile_from_behaviors(
                db, user_id, profile_updates
            )
    
    async def _update_profile_from_communication(self, db: AsyncSession, user_id: uuid.UUID, 
                                               style_profile: Dict[str, Any]):
        """Update cognitive profile based on communication style"""
        profile_updates = {}
        
        # Map communication styles to personality traits
        style_map = {
            "professional_assertive": {"conscientiousness": 0.8, "extraversion": 0.7},
            "professional_diplomatic": {"agreeableness": 0.8, "conscientiousness": 0.7},
            "casual_expressive": {"extraversion": 0.8, "openness": 0.7},
            "casual_direct": {"extraversion": 0.6, "conscientiousness": 0.5},
            "analytical_focused": {"conscientiousness": 0.8, "openness": 0.6},
            "balanced_adaptive": {"agreeableness": 0.7, "openness": 0.7}
        }
        
        primary_style = style_profile.get('primary_style')
        if primary_style in style_map:
            profile_updates = style_map[primary_style]
            await self.cognitive_service.update_profile_from_behaviors(
                db, user_id, profile_updates
            )
    
    async def _generate_ml_recommendations(self, db: AsyncSession, user_id: uuid.UUID, 
                                         insights: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on ML insights"""
        recommendations = []
        
        # Based on behavioral patterns
        patterns = insights.get("behavioral_patterns", [])
        if patterns:
            top_pattern = patterns[0]["pattern"]
            
            if top_pattern == "distracted_browsing":
                recommendations.append("Consider using website blockers during focus hours")
            elif top_pattern == "multitasking":
                recommendations.append("Try time-boxing tasks to improve focus")
            elif top_pattern == "productive_flow":
                recommendations.append("You're in a good flow - maintain your current routine")
        
        # Based on communication style
        comm_style = insights.get("communication_style")
        if comm_style:
            if comm_style.get("formality_level") == "casual" and comm_style.get("primary_style") == "casual_direct":
                recommendations.append("Consider adding more context in professional communications")
            elif comm_style.get("consistency_score", 1) < 0.5:
                recommendations.append("Your communication style varies - this shows good adaptability")
        
        return recommendations
    
    async def schedule_model_retraining(self, db: AsyncSession, user_id: uuid.UUID):
        """Schedule periodic model retraining"""
        # This would be implemented with a task queue (Celery) in production
        # For now, just log the intent
        logger.info(f"Scheduled model retraining for user {user_id}")
        
        # Store scheduling info
        await self.memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="procedural",
            content="Scheduled ML model retraining",
            source="ml_service",
            metadata={
                "scheduled_at": datetime.utcnow().isoformat(),
                "next_training": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )