import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from collections import defaultdict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import MemoryService
from app.services.cognitive_profile_service import CognitiveProfileService

logger = logging.getLogger(__name__)


class ActivityAnalyzer:
    """Analyzes screen activity patterns and updates user profile"""
    
    def __init__(self):
        self.memory_service = MemoryService()
        self.cognitive_service = CognitiveProfileService()
        self.activity_buffer = defaultdict(list)
        self.analysis_interval = 300  # 5 minutes
        
    async def process_screen_capture(self, user_id: str, capture_data: Dict[str, Any], db: AsyncSession):
        """Process a single screen capture"""
        # Add to buffer
        self.activity_buffer[user_id].append(capture_data)
        
        # Analyze if buffer is large enough
        if len(self.activity_buffer[user_id]) >= 10:
            await self.analyze_activity_batch(user_id, db)
    
    async def analyze_activity_batch(self, user_id: str, db: AsyncSession):
        """Analyze a batch of screen captures"""
        if user_id not in self.activity_buffer:
            return
        
        captures = self.activity_buffer[user_id]
        if not captures:
            return
        
        try:
            # Analyze patterns
            analysis = self._analyze_captures(captures)
            
            # Store insights as memories
            await self._store_activity_insights(user_id, analysis, db)
            
            # Update cognitive profile
            await self._update_profile_from_activity(user_id, analysis, db)
            
            # Clear processed captures
            self.activity_buffer[user_id] = []
            
        except Exception as e:
            logger.error(f"Error analyzing activity batch: {str(e)}")
    
    def _analyze_captures(self, captures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a batch of captures for patterns"""
        analysis = {
            "time_range": {
                "start": captures[0]["timestamp"],
                "end": captures[-1]["timestamp"]
            },
            "activity_distribution": defaultdict(int),
            "application_usage": defaultdict(int),
            "brightness_pattern": [],
            "focus_metrics": {},
            "multitasking_score": 0,
            "productivity_indicators": {}
        }
        
        # Count activity types
        for capture in captures:
            activity_type = capture.get("activity_type", "other")
            analysis["activity_distribution"][activity_type] += 1
            
            # Track application usage
            for app in capture.get("detected_applications", []):
                analysis["application_usage"][app] += 1
            
            # Track brightness
            analysis["brightness_pattern"].append(capture.get("brightness", 0.5))
        
        # Calculate focus metrics
        analysis["focus_metrics"] = self._calculate_focus_metrics(captures)
        
        # Calculate multitasking score
        analysis["multitasking_score"] = self._calculate_multitasking_score(captures)
        
        # Productivity indicators
        analysis["productivity_indicators"] = self._calculate_productivity_indicators(analysis)
        
        return analysis
    
    def _calculate_focus_metrics(self, captures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate focus-related metrics"""
        # Track activity type changes
        activity_changes = 0
        last_activity = None
        
        for capture in captures:
            current_activity = capture.get("activity_type")
            if last_activity and current_activity != last_activity:
                activity_changes += 1
            last_activity = current_activity
        
        # Calculate average session length per activity
        activity_sessions = defaultdict(list)
        current_activity = None
        session_start = None
        
        for i, capture in enumerate(captures):
            activity = capture.get("activity_type")
            
            if activity != current_activity:
                if current_activity and session_start is not None:
                    session_length = i - session_start
                    activity_sessions[current_activity].append(session_length)
                
                current_activity = activity
                session_start = i
        
        # Average session lengths
        avg_session_lengths = {}
        for activity, sessions in activity_sessions.items():
            if sessions:
                avg_session_lengths[activity] = np.mean(sessions)
        
        return {
            "activity_switches": activity_changes,
            "switch_rate": activity_changes / len(captures) if captures else 0,
            "average_session_lengths": avg_session_lengths,
            "focus_score": 1 - (activity_changes / len(captures)) if captures else 0
        }
    
    def _calculate_multitasking_score(self, captures: List[Dict[str, Any]]) -> float:
        """Calculate multitasking tendency score"""
        # Count unique applications per time window
        window_size = 5  # 5 captures
        app_diversity_scores = []
        
        for i in range(0, len(captures) - window_size + 1):
            window = captures[i:i + window_size]
            unique_apps = set()
            
            for capture in window:
                unique_apps.update(capture.get("detected_applications", []))
            
            diversity_score = len(unique_apps) / window_size
            app_diversity_scores.append(diversity_score)
        
        if app_diversity_scores:
            return np.mean(app_diversity_scores)
        return 0.0
    
    def _calculate_productivity_indicators(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate productivity-related indicators"""
        activity_dist = analysis["activity_distribution"]
        total_captures = sum(activity_dist.values())
        
        if total_captures == 0:
            return {}
        
        # Calculate productive time ratio
        productive_activities = ["coding", "document_work", "reading"]
        productive_captures = sum(activity_dist.get(act, 0) for act in productive_activities)
        productive_ratio = productive_captures / total_captures
        
        # Calculate distraction score
        distraction_activities = ["browsing", "communication"]
        distraction_captures = sum(activity_dist.get(act, 0) for act in distraction_activities)
        distraction_ratio = distraction_captures / total_captures
        
        # Work pattern (based on brightness as proxy for time of day)
        brightness_pattern = analysis.get("brightness_pattern", [])
        avg_brightness = np.mean(brightness_pattern) if brightness_pattern else 0.5
        
        return {
            "productive_time_ratio": productive_ratio,
            "distraction_ratio": distraction_ratio,
            "productivity_score": productive_ratio - (distraction_ratio * 0.5),
            "prefers_dark_mode": avg_brightness < 0.3,
            "consistency_score": 1 - np.std(brightness_pattern) if brightness_pattern else 0
        }
    
    async def _store_activity_insights(self, user_id: str, analysis: Dict[str, Any], db: AsyncSession):
        """Store activity insights as memories"""
        # Store activity distribution
        activity_dist = dict(analysis["activity_distribution"])
        if activity_dist:
            dominant_activity = max(activity_dist, key=activity_dist.get)
            
            await self.memory_service.store_memory(
                db,
                user_id=user_id,
                memory_type="semantic",
                content=f"Screen activity analysis shows primary focus on {dominant_activity}",
                source="screen_observer",
                metadata={
                    "activity_distribution": activity_dist,
                    "time_range": analysis["time_range"]
                }
            )
        
        # Store focus patterns
        focus_metrics = analysis.get("focus_metrics", {})
        if focus_metrics:
            focus_score = focus_metrics.get("focus_score", 0)
            
            await self.memory_service.store_memory(
                db,
                user_id=user_id,
                memory_type="semantic",
                content=f"Focus score: {focus_score:.2f}, with {focus_metrics.get('activity_switches', 0)} task switches",
                source="screen_observer",
                metadata={
                    "focus_metrics": focus_metrics
                }
            )
        
        # Store productivity insights
        productivity = analysis.get("productivity_indicators", {})
        if productivity:
            prod_score = productivity.get("productivity_score", 0)
            
            await self.memory_service.store_memory(
                db,
                user_id=user_id,
                memory_type="semantic",
                content=f"Productivity score: {prod_score:.2f}, productive time ratio: {productivity.get('productive_time_ratio', 0):.2f}",
                source="screen_observer",
                metadata={
                    "productivity_indicators": productivity
                }
            )
    
    async def _update_profile_from_activity(self, user_id: str, analysis: Dict[str, Any], db: AsyncSession):
        """Update cognitive profile based on screen activity"""
        profile_updates = {}
        
        # Focus score affects conscientiousness
        focus_score = analysis.get("focus_metrics", {}).get("focus_score", 0)
        if focus_score > 0.8:
            profile_updates["conscientiousness"] = 0.8
        elif focus_score < 0.4:
            profile_updates["conscientiousness"] = 0.4
        
        # Multitasking affects openness
        multitasking_score = analysis.get("multitasking_score", 0)
        if multitasking_score > 0.7:
            profile_updates["openness"] = 0.7
        
        # Activity diversity affects extraversion
        activity_types = len(analysis.get("activity_distribution", {}))
        if activity_types > 4:
            profile_updates["extraversion"] = 0.6
        elif activity_types < 2:
            profile_updates["extraversion"] = 0.3
        
        # Update profile
        if profile_updates:
            await self.cognitive_service.update_profile_from_behaviors(
                db, user_id, profile_updates
            )
    
    async def generate_daily_summary(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Generate daily activity summary"""
        # Query recent memories related to screen activity
        recent_memories = await self.memory_service.search_memories(
            db,
            user_id=user_id,
            memory_type="semantic",
            source_filter="screen_observer",
            limit=100
        )
        
        # Aggregate data from memories
        summary = {
            "date": datetime.utcnow().date().isoformat(),
            "total_observations": len(recent_memories),
            "activity_breakdown": defaultdict(int),
            "productivity_trend": [],
            "focus_trend": [],
            "recommendations": []
        }
        
        # Process memories
        for memory in recent_memories:
            metadata = memory.get("metadata", {})
            
            # Activity distribution
            if "activity_distribution" in metadata:
                for activity, count in metadata["activity_distribution"].items():
                    summary["activity_breakdown"][activity] += count
            
            # Productivity scores
            if "productivity_indicators" in metadata:
                prod_score = metadata["productivity_indicators"].get("productivity_score", 0)
                summary["productivity_trend"].append(prod_score)
            
            # Focus scores
            if "focus_metrics" in metadata:
                focus_score = metadata["focus_metrics"].get("focus_score", 0)
                summary["focus_trend"].append(focus_score)
        
        # Calculate averages
        if summary["productivity_trend"]:
            summary["average_productivity"] = np.mean(summary["productivity_trend"])
        
        if summary["focus_trend"]:
            summary["average_focus"] = np.mean(summary["focus_trend"])
        
        # Generate recommendations
        summary["recommendations"] = self._generate_recommendations(summary)
        
        return summary
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on activity patterns"""
        recommendations = []
        
        # Focus recommendations
        avg_focus = summary.get("average_focus", 0.5)
        if avg_focus < 0.5:
            recommendations.append("Consider using focus techniques like Pomodoro to reduce task switching")
        
        # Productivity recommendations
        avg_productivity = summary.get("average_productivity", 0.5)
        if avg_productivity < 0.5:
            recommendations.append("Try blocking distracting websites during work hours")
        
        # Activity balance
        activity_breakdown = dict(summary.get("activity_breakdown", {}))
        total_activities = sum(activity_breakdown.values())
        
        if total_activities > 0:
            browsing_ratio = activity_breakdown.get("browsing", 0) / total_activities
            if browsing_ratio > 0.4:
                recommendations.append("High browsing time detected - consider scheduled breaks")
        
        return recommendations