from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import numpy as np
from collections import Counter, defaultdict
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from textblob import TextBlob

from core.models.cognitive_profile import CognitiveProfile, ProfileAnalysisLog
from core.models.memory import Memory, MemoryType
from app.services.enhanced_nlp import EnhancedNLPService

logger = logging.getLogger(__name__)

class CognitiveProfileService:
    """Service for building and maintaining user cognitive profiles"""
    
    def __init__(self):
        self.nlp_service = EnhancedNLPService()
        
    async def get_or_create_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> CognitiveProfile:
        """Get existing profile or create a new one"""
        result = await db.execute(
            select(CognitiveProfile).where(CognitiveProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = CognitiveProfile(user_id=user_id)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            
        return profile
    
    async def analyze_user_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        force_full_analysis: bool = False
    ) -> Dict[str, Any]:
        """Analyze user's memories and interactions to build/update cognitive profile"""
        profile = await self.get_or_create_profile(db, user_id)
        
        # Determine if we need full analysis or incremental update
        if force_full_analysis or profile.analysis_count == 0:
            return await self._full_profile_analysis(db, user_id, profile)
        else:
            return await self._incremental_profile_update(db, user_id, profile)
    
    async def _full_profile_analysis(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        profile: CognitiveProfile
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis of all user data"""
        # Get all user memories
        result = await db.execute(
            select(Memory).where(Memory.user_id == user_id)
        )
        memories = result.scalars().all()
        
        if not memories:
            return {
                "status": "no_data",
                "message": "No memories found for analysis"
            }
        
        # Analyze different aspects
        personality_traits = await self._analyze_personality(memories)
        communication_style = await self._analyze_communication_style(memories)
        decision_patterns = await self._analyze_decision_making(memories)
        interests = await self._analyze_interests(memories)
        emotional_patterns = await self._analyze_emotional_patterns(memories)
        work_preferences = await self._analyze_work_preferences(memories)
        social_preferences = await self._analyze_social_preferences(memories)
        
        # Update profile
        updates = {
            # Personality traits
            "openness": personality_traits["openness"],
            "conscientiousness": personality_traits["conscientiousness"],
            "extraversion": personality_traits["extraversion"],
            "agreeableness": personality_traits["agreeableness"],
            "neuroticism": personality_traits["neuroticism"],
            
            # Communication
            "communication_formality": communication_style["formality"],
            "communication_verbosity": communication_style["verbosity"],
            "preferred_communication_channels": communication_style["channels"],
            
            # Decision making
            "decision_speed": decision_patterns["speed"],
            "risk_tolerance": decision_patterns["risk_tolerance"],
            "analytical_vs_intuitive": decision_patterns["analytical_score"],
            
            # Work and interests
            "work_style": work_preferences["style"],
            "peak_productivity_hours": work_preferences["peak_hours"],
            "preferred_task_types": work_preferences["task_types"],
            "interest_categories": interests["categories"],
            "expertise_areas": interests["expertise"],
            
            # Emotional and social
            "emotional_stability": emotional_patterns["stability"],
            "stress_triggers": emotional_patterns["triggers"],
            "coping_mechanisms": emotional_patterns["coping"],
            "social_energy": social_preferences["energy"],
            "relationship_depth": social_preferences["depth"],
            
            # Metadata
            "profile_confidence": self._calculate_confidence(len(memories)),
            "analysis_count": profile.analysis_count + 1,
            "data_points": len(memories)
        }
        
        # Apply updates to profile
        for key, value in updates.items():
            setattr(profile, key, value)
        
        # Log analysis
        analysis_log = ProfileAnalysisLog(
            profile_id=profile.id,
            analysis_type="full_analysis",
            source_data={"memory_count": len(memories)},
            results=updates,
            adjustments=updates,
            confidence=updates["profile_confidence"]
        )
        db.add(analysis_log)
        
        await db.commit()
        await db.refresh(profile)
        
        return {
            "status": "success",
            "profile": self._serialize_profile(profile),
            "analysis_summary": {
                "memories_analyzed": len(memories),
                "confidence": updates["profile_confidence"],
                "dominant_traits": self._get_dominant_traits(profile)
            }
        }
    
    async def _analyze_personality(self, memories: List[Memory]) -> Dict[str, float]:
        """Analyze Big Five personality traits from memories"""
        traits = {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5
        }
        
        # Keywords and patterns for each trait
        trait_indicators = {
            "openness": {
                "positive": ["creative", "curious", "explore", "new", "innovative", "art", "imagine", "adventure"],
                "negative": ["routine", "traditional", "conservative", "familiar"]
            },
            "conscientiousness": {
                "positive": ["organized", "plan", "schedule", "complete", "responsible", "detail", "thorough"],
                "negative": ["spontaneous", "flexible", "improvise", "casual"]
            },
            "extraversion": {
                "positive": ["social", "party", "friends", "group", "meeting", "talk", "energized"],
                "negative": ["alone", "quiet", "solitude", "introvert", "reserved"]
            },
            "agreeableness": {
                "positive": ["help", "kind", "cooperate", "trust", "empathy", "support", "care"],
                "negative": ["compete", "argue", "disagree", "conflict", "challenge"]
            },
            "neuroticism": {
                "positive": ["worry", "stress", "anxious", "upset", "nervous", "fear", "tense"],
                "negative": ["calm", "relaxed", "stable", "confident", "peaceful"]
            }
        }
        
        # Analyze each memory
        for memory in memories:
            content = memory.content.lower()
            sentiment = TextBlob(content).sentiment
            
            for trait, indicators in trait_indicators.items():
                positive_count = sum(1 for word in indicators["positive"] if word in content)
                negative_count = sum(1 for word in indicators["negative"] if word in content)
                
                # Adjust trait score
                if positive_count > negative_count:
                    traits[trait] = min(1.0, traits[trait] + 0.05)
                elif negative_count > positive_count:
                    traits[trait] = max(0.0, traits[trait] - 0.05)
                
                # Consider sentiment for neuroticism
                if trait == "neuroticism":
                    if sentiment.polarity < -0.3:
                        traits[trait] = min(1.0, traits[trait] + 0.03)
                    elif sentiment.polarity > 0.3:
                        traits[trait] = max(0.0, traits[trait] - 0.03)
        
        return traits
    
    async def _analyze_communication_style(self, memories: List[Memory]) -> Dict[str, Any]:
        """Analyze communication patterns and preferences"""
        formality_score = 0.5
        verbosity_scores = []
        channels = defaultdict(int)
        
        formal_indicators = ["please", "thank you", "regards", "sincerely", "mr", "ms", "dr"]
        informal_indicators = ["hey", "yeah", "cool", "awesome", "lol", "btw"]
        
        for memory in memories:
            content = memory.content.lower()
            
            # Formality analysis
            formal_count = sum(1 for word in formal_indicators if word in content)
            informal_count = sum(1 for word in informal_indicators if word in content)
            
            if formal_count > informal_count:
                formality_score = min(1.0, formality_score + 0.02)
            elif informal_count > formal_count:
                formality_score = max(0.0, formality_score - 0.02)
            
            # Verbosity analysis
            word_count = len(content.split())
            verbosity_scores.append(word_count)
            
            # Channel preferences from metadata
            if memory.meta_data:
                if "channel" in memory.meta_data:
                    channels[memory.meta_data["channel"]] += 1
                
                # Infer from content
                if "email" in content or "@" in content:
                    channels["email"] += 1
                elif "call" in content or "phone" in content:
                    channels["voice"] += 1
                elif "message" in content or "chat" in content:
                    channels["chat"] += 1
        
        # Calculate verbosity (normalized)
        avg_words = np.mean(verbosity_scores) if verbosity_scores else 50
        verbosity = min(1.0, avg_words / 200)  # Normalize to 0-1
        
        # Get top channels
        top_channels = sorted(channels.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "formality": formality_score,
            "verbosity": verbosity,
            "channels": [ch[0] for ch in top_channels] if top_channels else ["chat"]
        }
    
    async def _analyze_decision_making(self, memories: List[Memory]) -> Dict[str, float]:
        """Analyze decision-making patterns"""
        decision_memories = [m for m in memories if "decide" in m.content.lower() or "choice" in m.content.lower()]
        
        speed_indicators = {
            "fast": ["quickly", "immediately", "instant", "rapid", "spontaneous"],
            "slow": ["carefully", "considered", "analyzed", "researched", "deliberated"]
        }
        
        risk_indicators = {
            "high": ["risk", "chance", "gamble", "bold", "venture"],
            "low": ["safe", "secure", "conservative", "careful", "cautious"]
        }
        
        analytical_indicators = ["data", "analysis", "research", "facts", "evidence", "logic"]
        intuitive_indicators = ["feel", "gut", "instinct", "sense", "intuition"]
        
        speed_score = 0.5
        risk_score = 0.5
        analytical_score = 0.5
        
        for memory in decision_memories:
            content = memory.content.lower()
            
            # Decision speed
            fast_count = sum(1 for word in speed_indicators["fast"] if word in content)
            slow_count = sum(1 for word in speed_indicators["slow"] if word in content)
            
            if fast_count > slow_count:
                speed_score = min(1.0, speed_score + 0.1)
            elif slow_count > fast_count:
                speed_score = max(0.0, speed_score - 0.1)
            
            # Risk tolerance
            high_risk = sum(1 for word in risk_indicators["high"] if word in content)
            low_risk = sum(1 for word in risk_indicators["low"] if word in content)
            
            if high_risk > low_risk:
                risk_score = min(1.0, risk_score + 0.1)
            elif low_risk > high_risk:
                risk_score = max(0.0, risk_score - 0.1)
            
            # Analytical vs intuitive
            analytical_count = sum(1 for word in analytical_indicators if word in content)
            intuitive_count = sum(1 for word in intuitive_indicators if word in content)
            
            if analytical_count > intuitive_count:
                analytical_score = min(1.0, analytical_score + 0.1)
            elif intuitive_count > analytical_count:
                analytical_score = max(0.0, analytical_score - 0.1)
        
        return {
            "speed": speed_score,
            "risk_tolerance": risk_score,
            "analytical_score": analytical_score
        }
    
    async def _analyze_interests(self, memories: List[Memory]) -> Dict[str, Any]:
        """Analyze user interests and expertise areas"""
        interest_keywords = {
            "technology": ["code", "programming", "software", "computer", "tech", "app", "digital"],
            "sports": ["game", "play", "sport", "exercise", "fitness", "team", "match"],
            "arts": ["art", "music", "paint", "draw", "creative", "design", "aesthetic"],
            "science": ["research", "experiment", "study", "discover", "hypothesis", "data"],
            "business": ["meeting", "client", "project", "revenue", "strategy", "market"],
            "travel": ["trip", "visit", "travel", "explore", "destination", "journey"],
            "food": ["cook", "eat", "restaurant", "recipe", "meal", "taste", "cuisine"],
            "health": ["health", "wellness", "medical", "doctor", "exercise", "nutrition"],
            "education": ["learn", "study", "course", "teach", "education", "knowledge"],
            "social": ["friend", "family", "party", "social", "community", "relationship"]
        }
        
        interest_scores = defaultdict(float)
        expertise_mentions = defaultdict(int)
        
        for memory in memories:
            content = memory.content.lower()
            
            # Score interests
            for category, keywords in interest_keywords.items():
                matches = sum(1 for word in keywords if word in content)
                if matches > 0:
                    interest_scores[category] += matches
            
            # Extract expertise from metadata
            if memory.meta_data and "activity" in memory.meta_data:
                activities = memory.meta_data["activity"]
                if isinstance(activities, list):
                    for activity in activities:
                        expertise_mentions[activity] += 1
        
        # Normalize interest scores
        total_score = sum(interest_scores.values())
        if total_score > 0:
            interest_categories = {
                cat: score / total_score 
                for cat, score in interest_scores.items()
            }
        else:
            interest_categories = {}
        
        # Get top expertise areas
        expertise_areas = [
            area for area, count in sorted(
                expertise_mentions.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        ]
        
        return {
            "categories": dict(sorted(interest_categories.items(), key=lambda x: x[1], reverse=True)),
            "expertise": expertise_areas
        }
    
    async def _analyze_emotional_patterns(self, memories: List[Memory]) -> Dict[str, Any]:
        """Analyze emotional patterns and stability"""
        emotions = []
        stress_indicators = ["stress", "pressure", "overwhelm", "anxiety", "worry", "deadline"]
        coping_indicators = {
            "exercise": ["run", "gym", "workout", "exercise", "walk"],
            "meditation": ["meditate", "breathe", "calm", "relax", "mindful"],
            "social": ["talk", "friend", "support", "share", "vent"],
            "creative": ["write", "draw", "music", "create", "express"],
            "problem-solving": ["solve", "plan", "organize", "tackle", "address"]
        }
        
        triggers = defaultdict(int)
        coping_methods = defaultdict(int)
        
        for memory in memories:
            content = memory.content.lower()
            
            # Get sentiment
            sentiment = TextBlob(content).sentiment
            emotions.append(sentiment.polarity)
            
            # Identify stress triggers
            if any(indicator in content for indicator in stress_indicators):
                # Look for context
                if "deadline" in content:
                    triggers["deadlines"] += 1
                if "conflict" in content or "argument" in content:
                    triggers["conflict"] += 1
                if "work" in content:
                    triggers["work_pressure"] += 1
                if "change" in content:
                    triggers["change"] += 1
            
            # Identify coping mechanisms
            for method, keywords in coping_indicators.items():
                if any(keyword in content for keyword in keywords):
                    coping_methods[method] += 1
            
            # Check metadata for emotions
            if memory.meta_data and "emotions" in memory.meta_data:
                for emotion in memory.meta_data["emotions"]:
                    if emotion in ["angry", "frustrated", "upset"]:
                        emotions.append(-0.5)
                    elif emotion in ["happy", "excited", "grateful"]:
                        emotions.append(0.5)
        
        # Calculate emotional stability (inverse of variance)
        emotion_variance = np.var(emotions) if emotions else 0.5
        stability = max(0.0, min(1.0, 1.0 - emotion_variance))
        
        return {
            "stability": stability,
            "triggers": list(sorted(triggers.keys(), key=triggers.get, reverse=True)[:3]),
            "coping": list(sorted(coping_methods.keys(), key=coping_methods.get, reverse=True)[:3])
        }
    
    async def _analyze_work_preferences(self, memories: List[Memory]) -> Dict[str, Any]:
        """Analyze work style and preferences"""
        collaborative_keywords = ["team", "together", "collaborate", "meeting", "discuss", "we"]
        independent_keywords = ["alone", "myself", "independent", "solo", "own"]
        
        time_references = {
            "morning": ["morning", "am", "early", "breakfast"],
            "afternoon": ["afternoon", "lunch", "noon"],
            "evening": ["evening", "pm", "night", "dinner"],
            "late_night": ["midnight", "late night", "2am", "3am"]
        }
        
        task_types = {
            "creative": ["create", "design", "innovate", "imagine", "brainstorm"],
            "analytical": ["analyze", "data", "calculate", "measure", "evaluate"],
            "social": ["meet", "present", "communicate", "network", "collaborate"],
            "administrative": ["organize", "schedule", "document", "report", "manage"]
        }
        
        work_style_scores = {"collaborative": 0, "independent": 0}
        productivity_times = defaultdict(int)
        task_preferences = defaultdict(int)
        
        for memory in memories:
            content = memory.content.lower()
            
            # Work style
            collab_count = sum(1 for word in collaborative_keywords if word in content)
            indep_count = sum(1 for word in independent_keywords if word in content)
            
            work_style_scores["collaborative"] += collab_count
            work_style_scores["independent"] += indep_count
            
            # Productivity times
            for time_period, keywords in time_references.items():
                if any(keyword in content for keyword in keywords):
                    if "productive" in content or "work" in content or "complete" in content:
                        productivity_times[time_period] += 1
            
            # Task types
            for task_type, keywords in task_types.items():
                matches = sum(1 for word in keywords if word in content)
                if matches > 0:
                    task_preferences[task_type] += matches
        
        # Normalize work style
        total_style = sum(work_style_scores.values())
        if total_style > 0:
            work_style = {k: v/total_style for k, v in work_style_scores.items()}
        else:
            work_style = {"collaborative": 0.5, "independent": 0.5}
        
        # Get peak hours
        peak_hours = [
            time for time, count in sorted(
                productivity_times.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:2]
        ] or ["morning"]
        
        # Get preferred tasks
        preferred_tasks = [
            task for task, count in sorted(
                task_preferences.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
        ] or ["analytical"]
        
        return {
            "style": work_style,
            "peak_hours": peak_hours,
            "task_types": preferred_tasks
        }
    
    async def _analyze_social_preferences(self, memories: List[Memory]) -> Dict[str, Any]:
        """Analyze social preferences and patterns"""
        social_energy_indicators = {
            "extrovert": ["party", "social", "group", "crowd", "networking", "energized"],
            "introvert": ["alone", "quiet", "recharge", "solitude", "small group", "one-on-one"]
        }
        
        relationship_indicators = {
            "deep": ["close friend", "best friend", "deep conversation", "meaningful", "trust"],
            "broad": ["networking", "acquaintance", "meet new", "social circle", "connections"]
        }
        
        energy_score = 0.5
        depth_score = 0.5
        
        for memory in memories:
            content = memory.content.lower()
            
            # Social energy
            extro_count = sum(1 for word in social_energy_indicators["extrovert"] if word in content)
            intro_count = sum(1 for word in social_energy_indicators["introvert"] if word in content)
            
            if extro_count > intro_count:
                energy_score = min(1.0, energy_score + 0.05)
            elif intro_count > extro_count:
                energy_score = max(0.0, energy_score - 0.05)
            
            # Relationship depth
            deep_count = sum(1 for word in relationship_indicators["deep"] if word in content)
            broad_count = sum(1 for word in relationship_indicators["broad"] if word in content)
            
            if deep_count > broad_count:
                depth_score = min(1.0, depth_score + 0.05)
            elif broad_count > deep_count:
                depth_score = max(0.0, depth_score - 0.05)
        
        return {
            "energy": energy_score,
            "depth": depth_score
        }
    
    async def _incremental_profile_update(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        profile: CognitiveProfile
    ) -> Dict[str, Any]:
        """Update profile based on recent memories only"""
        # Get memories since last update
        last_update = profile.last_updated
        result = await db.execute(
            select(Memory)
            .where(
                and_(
                    Memory.user_id == user_id,
                    Memory.created_at > last_update
                )
            )
        )
        new_memories = result.scalars().all()
        
        if not new_memories:
            return {
                "status": "no_new_data",
                "message": "No new memories to analyze"
            }
        
        # Perform incremental analysis
        # This is a simplified version - in production, you'd weight
        # new data against existing profile
        
        new_traits = await self._analyze_personality(new_memories)
        
        # Blend with existing traits (weighted average)
        weight_old = 0.8
        weight_new = 0.2
        
        updates = {}
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            old_value = getattr(profile, trait)
            new_value = new_traits[trait]
            updates[trait] = (old_value * weight_old) + (new_value * weight_new)
        
        # Update profile
        for key, value in updates.items():
            setattr(profile, key, value)
        
        profile.data_points += len(new_memories)
        profile.analysis_count += 1
        
        await db.commit()
        await db.refresh(profile)
        
        return {
            "status": "success",
            "update_type": "incremental",
            "new_memories_analyzed": len(new_memories),
            "profile": self._serialize_profile(profile)
        }
    
    def _calculate_confidence(self, data_points: int) -> float:
        """Calculate confidence score based on data points"""
        # Logarithmic scale - more data points = higher confidence
        # Caps at 0.95
        if data_points == 0:
            return 0.0
        
        confidence = min(0.95, np.log(data_points + 1) / 10)
        return round(confidence, 2)
    
    def _get_dominant_traits(self, profile: CognitiveProfile) -> List[Dict[str, Any]]:
        """Get the most prominent traits of the user"""
        traits = []
        
        # Personality
        personality = {
            "openness": profile.openness,
            "conscientiousness": profile.conscientiousness,
            "extraversion": profile.extraversion,
            "agreeableness": profile.agreeableness,
            "neuroticism": profile.neuroticism
        }
        
        dominant_personality = max(personality.items(), key=lambda x: abs(x[1] - 0.5))
        if abs(dominant_personality[1] - 0.5) > 0.2:
            traits.append({
                "category": "personality",
                "trait": dominant_personality[0],
                "strength": dominant_personality[1]
            })
        
        # Communication
        if profile.communication_formality > 0.7:
            traits.append({
                "category": "communication",
                "trait": "formal",
                "strength": profile.communication_formality
            })
        elif profile.communication_formality < 0.3:
            traits.append({
                "category": "communication",
                "trait": "informal",
                "strength": 1 - profile.communication_formality
            })
        
        # Decision making
        if profile.analytical_vs_intuitive > 0.7:
            traits.append({
                "category": "decision_making",
                "trait": "analytical",
                "strength": profile.analytical_vs_intuitive
            })
        elif profile.analytical_vs_intuitive < 0.3:
            traits.append({
                "category": "decision_making",
                "trait": "intuitive",
                "strength": 1 - profile.analytical_vs_intuitive
            })
        
        return traits
    
    def _serialize_profile(self, profile: CognitiveProfile) -> Dict[str, Any]:
        """Convert profile to dictionary for API response"""
        return {
            "personality": {
                "openness": profile.openness,
                "conscientiousness": profile.conscientiousness,
                "extraversion": profile.extraversion,
                "agreeableness": profile.agreeableness,
                "neuroticism": profile.neuroticism
            },
            "communication": {
                "formality": profile.communication_formality,
                "verbosity": profile.communication_verbosity,
                "preferred_channels": profile.preferred_communication_channels
            },
            "decision_making": {
                "speed": profile.decision_speed,
                "risk_tolerance": profile.risk_tolerance,
                "style": "analytical" if profile.analytical_vs_intuitive > 0.5 else "intuitive",
                "analytical_score": profile.analytical_vs_intuitive
            },
            "work_preferences": {
                "style": profile.work_style,
                "peak_hours": profile.peak_productivity_hours,
                "task_types": profile.preferred_task_types
            },
            "interests": {
                "categories": profile.interest_categories,
                "expertise": profile.expertise_areas
            },
            "emotional_patterns": {
                "stability": profile.emotional_stability,
                "stress_triggers": profile.stress_triggers,
                "coping_mechanisms": profile.coping_mechanisms
            },
            "social_preferences": {
                "energy": profile.social_energy,
                "introvert_extrovert": "extrovert" if profile.social_energy > 0.5 else "introvert",
                "relationship_depth": profile.relationship_depth
            },
            "metadata": {
                "confidence": profile.profile_confidence,
                "last_updated": profile.last_updated.isoformat() if profile.last_updated else None,
                "data_points": profile.data_points,
                "analysis_count": profile.analysis_count
            }
        }
    
    async def get_profile_insights(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get actionable insights based on cognitive profile"""
        profile = await self.get_or_create_profile(db, user_id)
        
        if profile.analysis_count == 0:
            return {
                "status": "no_profile",
                "message": "Profile not yet analyzed"
            }
        
        insights = []
        
        # Personality insights
        if profile.openness > 0.7:
            insights.append({
                "type": "personality",
                "insight": "You're highly open to new experiences. Consider exploring creative projects or learning new skills.",
                "recommendations": ["Try new technologies", "Explore creative hobbies", "Travel to new places"]
            })
        
        if profile.conscientiousness > 0.7:
            insights.append({
                "type": "personality",
                "insight": "Your high conscientiousness makes you reliable and organized. Use this strength for complex projects.",
                "recommendations": ["Lead project planning", "Create systematic workflows", "Mentor others in organization"]
            })
        
        # Work insights
        if profile.peak_productivity_hours:
            peak_time = profile.peak_productivity_hours[0]
            insights.append({
                "type": "productivity",
                "insight": f"You're most productive during {peak_time}. Schedule important tasks during this time.",
                "recommendations": [f"Block {peak_time} for deep work", "Schedule meetings outside peak hours"]
            })
        
        # Social insights
        if profile.social_energy < 0.3:
            insights.append({
                "type": "social",
                "insight": "You prefer smaller, intimate settings. Honor this preference for better well-being.",
                "recommendations": ["Schedule regular alone time", "Prefer one-on-one meetings", "Create quiet workspaces"]
            })
        
        # Stress management
        if profile.stress_triggers and profile.coping_mechanisms:
            insights.append({
                "type": "wellness",
                "insight": f"Your main stress triggers include {', '.join(profile.stress_triggers[:2])}.",
                "recommendations": [f"Use {coping} when stressed" for coping in profile.coping_mechanisms[:2]]
            })
        
        return {
            "profile": self._serialize_profile(profile),
            "insights": insights,
            "dominant_traits": self._get_dominant_traits(profile)
        }