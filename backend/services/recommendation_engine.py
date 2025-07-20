import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import uuid
import numpy as np
from collections import defaultdict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.services.memory_service import MemoryService
from app.services.cognitive_profile_service import CognitiveProfileService
from services.ml_service import MLService
from core.models.user import User
from core.models.memory import Memory
from core.models.cognitive_profile import CognitiveProfile

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Engine for generating personalized decision recommendations"""
    
    def __init__(self):
        self.memory_service = MemoryService()
        self.cognitive_service = CognitiveProfileService()
        self.ml_service = MLService()
        
        # Decision categories
        self.decision_categories = {
            'productivity': ['work_schedule', 'task_prioritization', 'break_timing', 'focus_optimization'],
            'communication': ['email_timing', 'meeting_scheduling', 'response_style', 'contact_frequency'],
            'wellness': ['work_life_balance', 'stress_management', 'energy_optimization', 'habit_formation'],
            'learning': ['skill_development', 'information_consumption', 'knowledge_retention', 'learning_schedule'],
            'social': ['relationship_maintenance', 'networking', 'collaboration', 'boundary_setting']
        }
        
    async def generate_recommendations(self, db: AsyncSession, user_id: uuid.UUID, 
                                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive recommendations based on user patterns"""
        try:
            # Gather all relevant data
            user_data = await self._gather_user_data(db, user_id)
            
            if not user_data:
                return {"error": "Insufficient user data for recommendations"}
            
            # Generate recommendations by category
            recommendations = {}
            
            # Productivity recommendations
            recommendations['productivity'] = await self._generate_productivity_recommendations(
                db, user_id, user_data, context
            )
            
            # Communication recommendations
            recommendations['communication'] = await self._generate_communication_recommendations(
                db, user_id, user_data, context
            )
            
            # Wellness recommendations
            recommendations['wellness'] = await self._generate_wellness_recommendations(
                db, user_id, user_data, context
            )
            
            # Learning recommendations
            recommendations['learning'] = await self._generate_learning_recommendations(
                db, user_id, user_data, context
            )
            
            # Context-specific recommendations
            if context:
                recommendations['contextual'] = await self._generate_contextual_recommendations(
                    db, user_id, user_data, context
                )
            
            # Store recommendations as memory
            await self._store_recommendations(db, user_id, recommendations)
            
            return {
                "status": "success",
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat(),
                "confidence_score": self._calculate_confidence_score(user_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {"error": str(e)}
    
    async def _gather_user_data(self, db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Gather all relevant user data for recommendations"""
        data = {}
        
        # Get cognitive profile
        result = await db.execute(
            select(CognitiveProfile).where(CognitiveProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            data['cognitive_profile'] = {
                'openness': profile.openness,
                'conscientiousness': profile.conscientiousness,
                'extraversion': profile.extraversion,
                'agreeableness': profile.agreeableness,
                'neuroticism': profile.neuroticism,
                'work_style': profile.work_style,
                'decision_style': profile.decision_style,
                'stress_response': profile.stress_response
            }
        
        # Get recent behavioral patterns
        behavioral_insights = await self.ml_service.get_behavioral_insights(db, user_id)
        data['behavioral_patterns'] = behavioral_insights.get('behavioral_patterns', [])
        data['communication_style'] = behavioral_insights.get('communication_style')
        
        # Get recent memories for context
        recent_memories = await self.memory_service.search_memories(
            db, user_id, limit=100
        )
        data['recent_memories'] = recent_memories
        
        # Get integration data
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user and user.integrations_data:
            data['integrations'] = user.integrations_data
        
        return data
    
    async def _generate_productivity_recommendations(self, db: AsyncSession, user_id: uuid.UUID,
                                                   user_data: Dict[str, Any], 
                                                   context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate productivity-related recommendations"""
        recommendations = []
        
        # Analyze behavioral patterns
        patterns = user_data.get('behavioral_patterns', [])
        profile = user_data.get('cognitive_profile', {})
        
        # Time management recommendations
        if patterns:
            top_pattern = patterns[0]['pattern'] if patterns else None
            
            if top_pattern == 'distracted_browsing':
                recommendations.append({
                    'type': 'time_management',
                    'title': 'Implement Time Blocking',
                    'description': 'Your browsing patterns suggest frequent context switching. Try 25-minute focused work blocks.',
                    'action_items': [
                        'Use Pomodoro technique: 25 min work, 5 min break',
                        'Block distracting websites during focus hours',
                        'Schedule specific times for email and browsing'
                    ],
                    'priority': 'high',
                    'expected_impact': 'Increase focus time by 40%'
                })
            
            elif top_pattern == 'deep_focus':
                recommendations.append({
                    'type': 'optimization',
                    'title': 'Optimize Your Flow State',
                    'description': 'You excel at deep work. Maximize these periods.',
                    'action_items': [
                        'Protect your morning hours for complex tasks',
                        'Batch similar tasks together',
                        'Use "Do Not Disturb" mode during focus sessions'
                    ],
                    'priority': 'medium',
                    'expected_impact': 'Maintain current high productivity'
                })
        
        # Task prioritization based on personality
        if profile.get('conscientiousness', 0.5) < 0.4:
            recommendations.append({
                'type': 'task_management',
                'title': 'Simplify Task Prioritization',
                'description': 'A simple system will help you stay on track without feeling overwhelmed.',
                'action_items': [
                    'Use the 2-minute rule: do it now if it takes less than 2 minutes',
                    'Keep a maximum of 3 priority tasks per day',
                    'Review and adjust priorities each morning'
                ],
                'priority': 'high',
                'expected_impact': 'Reduce task overwhelm by 50%'
            })
        
        # Energy management
        if 'calendar' in user_data.get('integrations', {}):
            recommendations.append({
                'type': 'energy_management',
                'title': 'Align Tasks with Energy Levels',
                'description': 'Schedule demanding tasks during your peak hours.',
                'action_items': [
                    'Track energy levels for one week',
                    'Schedule creative work during high-energy periods',
                    'Reserve routine tasks for low-energy times'
                ],
                'priority': 'medium',
                'expected_impact': 'Improve task completion rate by 25%'
            })
        
        return recommendations
    
    async def _generate_communication_recommendations(self, db: AsyncSession, user_id: uuid.UUID,
                                                    user_data: Dict[str, Any], 
                                                    context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate communication-related recommendations"""
        recommendations = []
        
        comm_style = user_data.get('communication_style')
        profile = user_data.get('cognitive_profile', {})
        
        if comm_style:
            # Email timing optimization
            if comm_style.get('formality_level') == 'formal':
                recommendations.append({
                    'type': 'email_optimization',
                    'title': 'Optimize Email Communication',
                    'description': 'Your formal style is professional but may benefit from occasional warmth.',
                    'action_items': [
                        'Add a personal touch in the opening line',
                        'Use the recipient\'s name once per email',
                        'Consider time zones when sending emails'
                    ],
                    'priority': 'low',
                    'expected_impact': 'Improve response rates by 15%'
                })
            
            # Response time management
            if profile.get('conscientiousness', 0.5) > 0.7:
                recommendations.append({
                    'type': 'boundary_setting',
                    'title': 'Set Communication Boundaries',
                    'description': 'Your high responsiveness may lead to burnout.',
                    'action_items': [
                        'Set specific email checking times (e.g., 9am, 1pm, 5pm)',
                        'Use auto-responders for focused work periods',
                        'Delay non-urgent responses to batch processing times'
                    ],
                    'priority': 'medium',
                    'expected_impact': 'Reduce interruptions by 60%'
                })
        
        # Meeting optimization
        if profile.get('extraversion', 0.5) < 0.4:
            recommendations.append({
                'type': 'meeting_management',
                'title': 'Optimize Meeting Participation',
                'description': 'Prepare strategies for more comfortable meeting participation.',
                'action_items': [
                    'Request agendas in advance to prepare thoughts',
                    'Use written follow-ups to share additional insights',
                    'Schedule buffer time after meetings to recharge'
                ],
                'priority': 'medium',
                'expected_impact': 'Increase meeting satisfaction by 30%'
            })
        
        return recommendations
    
    async def _generate_wellness_recommendations(self, db: AsyncSession, user_id: uuid.UUID,
                                               user_data: Dict[str, Any], 
                                               context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate wellness and work-life balance recommendations"""
        recommendations = []
        
        profile = user_data.get('cognitive_profile', {})
        patterns = user_data.get('behavioral_patterns', [])
        
        # Stress management
        if profile.get('neuroticism', 0.5) > 0.6 or profile.get('stress_response') == 'overwhelm':
            recommendations.append({
                'type': 'stress_management',
                'title': 'Implement Stress Reduction Techniques',
                'description': 'Your profile suggests you may benefit from structured stress management.',
                'action_items': [
                    'Practice 5-minute breathing exercises during transitions',
                    'Schedule regular breaks every 90 minutes',
                    'End workday with a "shutdown ritual"'
                ],
                'priority': 'high',
                'expected_impact': 'Reduce stress levels by 35%'
            })
        
        # Work-life balance
        evening_work_pattern = any(p['pattern'] == 'productive_flow' for p in patterns)
        if evening_work_pattern:
            recommendations.append({
                'type': 'work_life_balance',
                'title': 'Establish Work-Life Boundaries',
                'description': 'Late work sessions may impact rest and recovery.',
                'action_items': [
                    'Set a firm end time for work activities',
                    'Create an evening routine that doesn\'t involve screens',
                    'Use separate devices/accounts for work and personal'
                ],
                'priority': 'high',
                'expected_impact': 'Improve sleep quality and energy levels'
            })
        
        # Energy optimization
        recommendations.append({
            'type': 'energy_management',
            'title': 'Optimize Daily Energy Rhythms',
            'description': 'Align activities with your natural energy patterns.',
            'action_items': [
                'Track energy levels hourly for one week',
                'Identify your peak performance windows',
                'Schedule breaks before energy crashes'
            ],
            'priority': 'medium',
            'expected_impact': 'Increase sustained energy by 20%'
        })
        
        return recommendations
    
    async def _generate_learning_recommendations(self, db: AsyncSession, user_id: uuid.UUID,
                                               user_data: Dict[str, Any], 
                                               context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate learning and development recommendations"""
        recommendations = []
        
        profile = user_data.get('cognitive_profile', {})
        patterns = user_data.get('behavioral_patterns', [])
        
        # Learning style optimization
        if profile.get('openness', 0.5) > 0.7:
            recommendations.append({
                'type': 'skill_development',
                'title': 'Diversify Learning Approaches',
                'description': 'Your high openness suggests you\'ll benefit from varied learning methods.',
                'action_items': [
                    'Alternate between reading, video, and hands-on learning',
                    'Join communities related to your interests',
                    'Set monthly learning challenges'
                ],
                'priority': 'medium',
                'expected_impact': 'Accelerate skill acquisition by 40%'
            })
        
        # Information consumption
        browsing_pattern = any(p['pattern'] == 'learning_research' for p in patterns)
        if browsing_pattern:
            recommendations.append({
                'type': 'information_management',
                'title': 'Optimize Information Consumption',
                'description': 'Structure your research for better retention.',
                'action_items': [
                    'Use the Zettelkasten method for note-taking',
                    'Schedule weekly review sessions',
                    'Create summaries after each learning session'
                ],
                'priority': 'medium',
                'expected_impact': 'Improve knowledge retention by 50%'
            })
        
        return recommendations
    
    async def _generate_contextual_recommendations(self, db: AsyncSession, user_id: uuid.UUID,
                                                  user_data: Dict[str, Any], 
                                                  context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate context-specific recommendations"""
        recommendations = []
        
        # Decision context
        if context.get('decision_type'):
            decision_type = context['decision_type']
            profile = user_data.get('cognitive_profile', {})
            
            if decision_type == 'career':
                if profile.get('decision_style') == 'analytical':
                    recommendations.append({
                        'type': 'decision_support',
                        'title': 'Structured Career Decision Framework',
                        'description': 'Use your analytical strengths for this decision.',
                        'action_items': [
                            'Create a weighted decision matrix',
                            'Research industry trends and projections',
                            'Conduct informational interviews',
                            'Set a decision deadline to avoid analysis paralysis'
                        ],
                        'priority': 'high',
                        'expected_impact': 'Make confident decision with 90% clarity'
                    })
            
            elif decision_type == 'purchase':
                recommendations.append({
                    'type': 'decision_support',
                    'title': 'Smart Purchase Decision Process',
                    'description': 'Apply your typical decision patterns effectively.',
                    'action_items': [
                        'Research at least 3 alternatives',
                        'Read reviews from similar users',
                        'Calculate true cost of ownership',
                        'Sleep on it if over $500'
                    ],
                    'priority': 'medium',
                    'expected_impact': 'Increase purchase satisfaction by 80%'
                })
        
        # Time-based context
        if context.get('time_pressure'):
            recommendations.append({
                'type': 'quick_decision',
                'title': 'Rapid Decision Framework',
                'description': 'Make quality decisions under time pressure.',
                'action_items': [
                    'List must-haves vs nice-to-haves',
                    'Set a timer for research phase',
                    'Trust your intuition for final call',
                    'Plan to iterate if needed'
                ],
                'priority': 'high',
                'expected_impact': 'Reduce decision time by 70%'
            })
        
        return recommendations
    
    async def get_decision_support(self, db: AsyncSession, user_id: uuid.UUID,
                                 decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific decision support based on context"""
        try:
            # Gather historical decisions
            decision_memories = await self.memory_service.search_memories(
                db,
                user_id=user_id,
                content_query="decision",
                limit=50
            )
            
            # Analyze past decision patterns
            decision_analysis = self._analyze_decision_history(decision_memories)
            
            # Get user profile
            user_data = await self._gather_user_data(db, user_id)
            
            # Generate decision framework
            framework = self._create_decision_framework(
                user_data,
                decision_analysis,
                decision_context
            )
            
            # Generate specific recommendations
            recommendations = await self._generate_contextual_recommendations(
                db, user_id, user_data, decision_context
            )
            
            return {
                "decision_framework": framework,
                "historical_insights": decision_analysis,
                "recommendations": recommendations,
                "confidence_factors": self._identify_confidence_factors(
                    user_data, decision_context
                )
            }
            
        except Exception as e:
            logger.error(f"Error providing decision support: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_decision_history(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical decision patterns"""
        decision_patterns = {
            'decision_speed': [],
            'satisfaction_levels': [],
            'decision_factors': defaultdict(int),
            'regret_patterns': []
        }
        
        for memory in memories:
            content = memory.get('content', '').lower()
            metadata = memory.get('metadata', {})
            
            # Extract decision characteristics
            if 'quick' in content or 'fast' in content:
                decision_patterns['decision_speed'].append('quick')
            elif 'careful' in content or 'deliberate' in content:
                decision_patterns['decision_speed'].append('deliberate')
            
            # Look for satisfaction indicators
            if 'happy' in content or 'satisfied' in content or 'good decision' in content:
                decision_patterns['satisfaction_levels'].append('high')
            elif 'regret' in content or 'mistake' in content:
                decision_patterns['satisfaction_levels'].append('low')
                decision_patterns['regret_patterns'].append(memory)
            
            # Extract decision factors
            if 'cost' in content or 'price' in content:
                decision_patterns['decision_factors']['cost'] += 1
            if 'quality' in content:
                decision_patterns['decision_factors']['quality'] += 1
            if 'time' in content:
                decision_patterns['decision_factors']['time'] += 1
        
        # Calculate success rate
        total_decisions = len(decision_patterns['satisfaction_levels'])
        if total_decisions > 0:
            success_rate = decision_patterns['satisfaction_levels'].count('high') / total_decisions
        else:
            success_rate = 0.5
        
        return {
            'success_rate': success_rate,
            'typical_speed': max(set(decision_patterns['decision_speed']), 
                               key=decision_patterns['decision_speed'].count) if decision_patterns['decision_speed'] else 'moderate',
            'key_factors': dict(decision_patterns['decision_factors']),
            'common_regrets': self._summarize_regret_patterns(decision_patterns['regret_patterns'])
        }
    
    def _summarize_regret_patterns(self, regret_memories: List[Dict[str, Any]]) -> List[str]:
        """Summarize common regret patterns"""
        patterns = []
        
        if len(regret_memories) > 0:
            # Extract common themes
            rushed_decisions = sum(1 for m in regret_memories if 'rush' in m.get('content', '').lower())
            if rushed_decisions > len(regret_memories) * 0.3:
                patterns.append("Decisions made under time pressure often lead to regret")
            
            emotional_decisions = sum(1 for m in regret_memories if any(
                word in m.get('content', '').lower() 
                for word in ['emotional', 'angry', 'excited', 'stressed']
            ))
            if emotional_decisions > len(regret_memories) * 0.3:
                patterns.append("Decisions made during emotional states need extra consideration")
        
        return patterns
    
    def _create_decision_framework(self, user_data: Dict[str, Any],
                                 decision_analysis: Dict[str, Any],
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized decision framework"""
        profile = user_data.get('cognitive_profile', {})
        
        # Base framework
        framework = {
            'steps': [],
            'time_allocation': {},
            'key_considerations': [],
            'decision_tools': []
        }
        
        # Customize based on decision style
        if profile.get('decision_style') == 'analytical':
            framework['steps'] = [
                'Define decision criteria and weights',
                'Research all available options',
                'Create comparison matrix',
                'Calculate weighted scores',
                'Validate with trusted advisor',
                'Make final decision'
            ]
            framework['time_allocation'] = {
                'research': '40%',
                'analysis': '30%',
                'validation': '20%',
                'decision': '10%'
            }
            framework['decision_tools'] = [
                'Decision matrix template',
                'Cost-benefit analysis',
                'Risk assessment checklist'
            ]
            
        elif profile.get('decision_style') == 'intuitive':
            framework['steps'] = [
                'Clarify core values and goals',
                'Gather essential information',
                'Reflect on gut feeling',
                'Visualize outcomes',
                'Check alignment with values',
                'Commit to decision'
            ]
            framework['time_allocation'] = {
                'clarification': '20%',
                'information': '30%',
                'reflection': '30%',
                'decision': '20%'
            }
            framework['decision_tools'] = [
                'Values alignment checklist',
                'Visualization exercises',
                'Pros and cons list'
            ]
        
        else:  # Balanced
            framework['steps'] = [
                'Define the decision clearly',
                'Identify key stakeholders',
                'Research main options',
                'List pros and cons',
                'Check gut feeling',
                'Make and commit to decision'
            ]
            framework['time_allocation'] = {
                'definition': '15%',
                'research': '35%',
                'analysis': '25%',
                'intuition': '15%',
                'decision': '10%'
            }
        
        # Add context-specific considerations
        if context.get('decision_type') == 'financial':
            framework['key_considerations'].extend([
                'Long-term financial impact',
                'Opportunity cost',
                'Risk tolerance alignment'
            ])
        elif context.get('decision_type') == 'career':
            framework['key_considerations'].extend([
                'Skills and growth alignment',
                'Work-life balance impact',
                'Long-term career trajectory'
            ])
        
        return framework
    
    def _identify_confidence_factors(self, user_data: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Identify factors that increase decision confidence"""
        profile = user_data.get('cognitive_profile', {})
        
        confidence_factors = {
            'strengths': [],
            'watch_points': [],
            'confidence_boosters': []
        }
        
        # Identify strengths
        if profile.get('conscientiousness', 0.5) > 0.6:
            confidence_factors['strengths'].append('Thorough research and preparation')
        
        if profile.get('openness', 0.5) > 0.6:
            confidence_factors['strengths'].append('Considering creative alternatives')
        
        # Identify watch points
        if profile.get('neuroticism', 0.5) > 0.6:
            confidence_factors['watch_points'].append('Anxiety may cloud judgment - use calming techniques')
        
        if profile.get('decision_style') == 'analytical':
            confidence_factors['watch_points'].append('Avoid analysis paralysis - set decision deadline')
        
        # Confidence boosters
        confidence_factors['confidence_boosters'] = [
            'Review past successful decisions',
            'Consult with trusted advisors',
            'Set clear decision criteria upfront',
            'Trust your prepared framework'
        ]
        
        return confidence_factors
    
    def _calculate_confidence_score(self, user_data: Dict[str, Any]) -> float:
        """Calculate confidence score for recommendations"""
        score = 0.5  # Base score
        
        # More data increases confidence
        if user_data.get('behavioral_patterns'):
            score += 0.1
        
        if user_data.get('cognitive_profile'):
            score += 0.1
        
        if user_data.get('communication_style'):
            score += 0.1
        
        # Recent memories increase relevance
        recent_memories = user_data.get('recent_memories', [])
        if len(recent_memories) > 50:
            score += 0.1
        
        # Cap at 0.9
        return min(score, 0.9)
    
    async def _store_recommendations(self, db: AsyncSession, user_id: uuid.UUID,
                                   recommendations: Dict[str, Any]):
        """Store generated recommendations as memory"""
        # Create summary of recommendations
        total_recs = sum(len(recs) for recs in recommendations.values() if isinstance(recs, list))
        
        high_priority = []
        for category, recs in recommendations.items():
            if isinstance(recs, list):
                high_priority.extend([r['title'] for r in recs if r.get('priority') == 'high'])
        
        summary = f"Generated {total_recs} recommendations. High priority: {', '.join(high_priority[:3])}"
        
        await self.memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="procedural",
            content=summary,
            source="recommendation_engine",
            metadata={
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat(),
                "high_priority_count": len(high_priority)
            }
        )