from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime, Enum as SQLEnum, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from core.database import Base

class MemoryType(str, enum.Enum):
    EPISODIC = "episodic"  # Specific events and experiences
    SEMANTIC = "semantic"  # General knowledge and facts
    PROCEDURAL = "procedural"  # How to do things
    SOCIAL = "social"  # Relationships and interactions
    CONVERSATION = "conversation"  # Chat history

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    memory_type = Column(SQLEnum(MemoryType), default=MemoryType.EPISODIC)
    meta_data = Column(JSON, default={})
    embedding = Column(JSON, nullable=True)  # Store vector embeddings
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    def __repr__(self):
        return f"<Memory {self.id}: {self.content[:50]}...>"

class MemoryRelation(Base):
    __tablename__ = "memory_relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id"), nullable=False)
    target_memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id"), nullable=False)
    relation_type = Column(String, nullable=False)  # e.g., "related_to", "caused_by", "happened_after"
    strength = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)