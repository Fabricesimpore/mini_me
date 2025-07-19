from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, String, cast
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import uuid

from core.models.memory import Memory, MemoryType, MemoryRelation
from core.models.user import User

class MemoryService:
    """Service for managing user memories"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def store_memory(
        self,
        user_id: uuid.UUID,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        meta_data: Dict[str, Any] = None,
        embedding: List[float] = None
    ) -> Memory:
        """Store a new memory"""
        memory = Memory(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            meta_data=meta_data or {},
            embedding=embedding
        )
        
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        
        # Create relations if needed
        self._create_memory_relations(memory)
        
        return memory
    
    def search_memories(
        self,
        user_id: uuid.UUID,
        query: str,
        memory_type: Optional[MemoryType] = None,
        time_range: Optional[Dict[str, datetime]] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories based on query and filters"""
        query_obj = self.db.query(Memory).filter(Memory.user_id == user_id)
        
        # Filter by memory type
        if memory_type:
            query_obj = query_obj.filter(Memory.memory_type == memory_type)
        
        # Filter by time range
        if time_range:
            if "start" in time_range:
                query_obj = query_obj.filter(Memory.created_at >= time_range["start"])
            if "end" in time_range:
                query_obj = query_obj.filter(Memory.created_at <= time_range["end"])
        
        # Simple text search (in production, use vector similarity)
        if query:
            search_terms = query.lower().split()
            for term in search_terms:
                query_obj = query_obj.filter(
                    or_(
                        Memory.content.ilike(f"%{term}%"),
                        Memory.meta_data.cast(String).ilike(f"%{term}%")
                    )
                )
        
        # Order by relevance (simple: most recent first)
        memories = query_obj.order_by(desc(Memory.created_at)).limit(limit).all()
        
        return memories
    
    def get_memories(
        self,
        user_id: uuid.UUID,
        memory_type: Optional[MemoryType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memory]:
        """Get memories for a user"""
        query = self.db.query(Memory).filter(Memory.user_id == user_id)
        
        if memory_type:
            query = query.filter(Memory.memory_type == memory_type)
        
        return query.order_by(desc(Memory.created_at)).limit(limit).offset(offset).all()
    
    def get_memory_by_id(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Memory]:
        """Get a specific memory"""
        return self.db.query(Memory).filter(
            and_(Memory.id == memory_id, Memory.user_id == user_id)
        ).first()
    
    def update_memory(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
        content: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Memory]:
        """Update an existing memory"""
        memory = self.get_memory_by_id(memory_id, user_id)
        if not memory:
            return None
        
        if content:
            memory.content = content
        if meta_data:
            memory.meta_data = meta_data
        
        memory.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(memory)
        
        return memory
    
    def delete_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a memory"""
        memory = self.get_memory_by_id(memory_id, user_id)
        if not memory:
            return False
        
        # Delete related relations
        self.db.query(MemoryRelation).filter(
            or_(
                MemoryRelation.source_memory_id == memory_id,
                MemoryRelation.target_memory_id == memory_id
            )
        ).delete()
        
        self.db.delete(memory)
        self.db.commit()
        
        return True
    
    def _create_memory_relations(self, memory: Memory):
        """Create relations between memories based on content and metadata"""
        # Find related memories (simple implementation)
        recent_memories = self.db.query(Memory).filter(
            and_(
                Memory.user_id == memory.user_id,
                Memory.id != memory.id,
                Memory.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).limit(20).all()
        
        for other_memory in recent_memories:
            # Check for common entities or topics
            if self._memories_are_related(memory, other_memory):
                relation = MemoryRelation(
                    source_memory_id=memory.id,
                    target_memory_id=other_memory.id,
                    relation_type="related_to",
                    strength=0.5
                )
                self.db.add(relation)
        
        self.db.commit()
    
    def _memories_are_related(self, memory1: Memory, memory2: Memory) -> bool:
        """Check if two memories are related (simple implementation)"""
        # Check for common words (excluding common words)
        common_words = {"the", "a", "an", "is", "are", "was", "were", "i", "you", "we", "they"}
        
        words1 = set(memory1.content.lower().split()) - common_words
        words2 = set(memory2.content.lower().split()) - common_words
        
        common = words1.intersection(words2)
        
        # If they share significant words, they might be related
        return len(common) >= 2
    
    def get_memory_stats(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get statistics about user's memories"""
        total_memories = self.db.query(Memory).filter(Memory.user_id == user_id).count()
        
        # Count by type
        type_counts = {}
        for memory_type in MemoryType:
            count = self.db.query(Memory).filter(
                and_(Memory.user_id == user_id, Memory.memory_type == memory_type)
            ).count()
            type_counts[memory_type.value] = count
        
        # Recent activity
        recent_count = self.db.query(Memory).filter(
            and_(
                Memory.user_id == user_id,
                Memory.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).count()
        
        return {
            "total_memories": total_memories,
            "by_type": type_counts,
            "recent_memories": recent_count,
            "last_memory": self.db.query(Memory).filter(Memory.user_id == user_id).order_by(desc(Memory.created_at)).first()
        }