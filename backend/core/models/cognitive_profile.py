from sqlalchemy import Column, String, Float, JSON, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base

class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Big Five Personality Traits (OCEAN)
    openness = Column(Float, default=0.5)  # 0-1 scale
    conscientiousness = Column(Float, default=0.5)
    extraversion = Column(Float, default=0.5)
    agreeableness = Column(Float, default=0.5)
    neuroticism = Column(Float, default=0.5)
    
    # Communication Style
    communication_formality = Column(Float, default=0.5)  # 0=informal, 1=formal
    communication_verbosity = Column(Float, default=0.5)  # 0=concise, 1=verbose
    preferred_communication_channels = Column(JSON, default=list)  # ["chat", "email", "voice"]
    
    # Decision Making Style
    decision_speed = Column(Float, default=0.5)  # 0=slow/deliberate, 1=fast/impulsive
    risk_tolerance = Column(Float, default=0.5)  # 0=risk-averse, 1=risk-seeking
    analytical_vs_intuitive = Column(Float, default=0.5)  # 0=intuitive, 1=analytical
    
    # Work Preferences
    work_style = Column(JSON, default=dict)  # {"collaborative": 0.7, "independent": 0.3}
    peak_productivity_hours = Column(JSON, default=list)  # ["morning", "evening"]
    preferred_task_types = Column(JSON, default=list)  # ["creative", "analytical", "social"]
    
    # Learning Style
    learning_preferences = Column(JSON, default=dict)  # {"visual": 0.4, "auditory": 0.3, "kinesthetic": 0.3}
    curiosity_level = Column(Float, default=0.5)
    
    # Social Preferences
    social_energy = Column(Float, default=0.5)  # 0=introvert, 1=extrovert
    relationship_depth = Column(Float, default=0.5)  # 0=many shallow, 1=few deep
    conflict_style = Column(JSON, default=dict)  # {"avoiding": 0.2, "accommodating": 0.3, ...}
    
    # Interests and Topics
    interest_categories = Column(JSON, default=dict)  # {"technology": 0.8, "sports": 0.3, ...}
    expertise_areas = Column(JSON, default=list)  # ["programming", "design", ...]
    
    # Emotional Patterns
    emotional_stability = Column(Float, default=0.5)
    stress_triggers = Column(JSON, default=list)  # ["deadlines", "conflict", ...]
    coping_mechanisms = Column(JSON, default=list)  # ["exercise", "meditation", ...]
    
    # Values and Motivations
    core_values = Column(JSON, default=list)  # ["family", "achievement", "creativity"]
    motivators = Column(JSON, default=dict)  # {"intrinsic": 0.7, "extrinsic": 0.3}
    
    # Behavioral Patterns
    routine_preference = Column(Float, default=0.5)  # 0=spontaneous, 1=routine-oriented
    multitasking_preference = Column(Float, default=0.5)  # 0=single-focus, 1=multitasker
    
    # Confidence Scores
    profile_confidence = Column(Float, default=0.0)  # Overall confidence in profile accuracy
    trait_confidences = Column(JSON, default=dict)  # Confidence for each trait
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analysis_count = Column(Float, default=0)  # Number of analyses performed
    data_points = Column(Float, default=0)  # Number of data points used
    
    # Relationships
    user = relationship("User", backref="cognitive_profile")

class ProfileAnalysisLog(Base):
    __tablename__ = "profile_analysis_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("cognitive_profiles.id"), nullable=False)
    analysis_type = Column(String)  # "personality", "communication", "interests", etc.
    source_data = Column(JSON)  # References to memories/interactions analyzed
    results = Column(JSON)  # Analysis results
    adjustments = Column(JSON)  # What changed in the profile
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("CognitiveProfile", backref="analysis_logs")