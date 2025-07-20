from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from core.models.memory import Memory, MemoryType, MemoryRelation
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class MemoryService:
    """Enhanced memory service with vector embeddings and semantic search"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        
    async def store_memory(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        confidence_score: float = 1.0
    ) -> Memory:
        """
        Store a memory with its embedding.
        
        Args:
            db: Database session
            user_id: User ID
            content: Memory content
            memory_type: Type of memory
            metadata: Additional metadata
            confidence_score: Confidence in the memory
            
        Returns:
            Created memory object
        """
        # Create embedding for the memory
        metadata = metadata or {}
        embedding = self.embedding_service.create_memory_embedding(content, metadata)
        
        # Create memory object
        memory = Memory(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            meta_data=metadata,
            embedding=embedding,
            confidence_score=confidence_score
        )
        
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        
        # Find and create relationships with existing memories
        await self._update_memory_relationships(db, memory)
        
        return memory
    
    async def semantic_search(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 20,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on memories using embeddings.
        
        Args:
            db: Database session
            user_id: User ID
            query: Search query
            memory_types: Optional filter by memory types
            time_range: Optional time range filter
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of memories with similarity scores
        """
        # Create query embedding with context
        context = {
            "memory_type": [mt.value for mt in memory_types] if memory_types else None,
            "time_range": f"{time_range[0]} to {time_range[1]}" if time_range else None
        }
        query_embedding = self.embedding_service.create_query_embedding(query, context)
        
        # Build base query
        base_query = select(Memory).where(Memory.user_id == user_id)
        
        # Apply filters
        if memory_types:
            base_query = base_query.where(Memory.memory_type.in_(memory_types))
        
        if time_range:
            base_query = base_query.where(
                and_(
                    Memory.created_at >= time_range[0],
                    Memory.created_at <= time_range[1]
                )
            )
        
        # Get all matching memories
        result = await db.execute(base_query)
        memories = result.scalars().all()
        
        # Calculate similarities
        memory_scores = []
        for memory in memories:
            if memory.embedding:
                similarity = self.embedding_service.calculate_similarity(
                    query_embedding,
                    memory.embedding
                )
                
                if similarity >= similarity_threshold:
                    memory_scores.append({
                        "memory": memory,
                        "similarity": similarity,
                        "id": str(memory.id),
                        "content": memory.content,
                        "type": memory.memory_type.value,
                        "metadata": memory.meta_data,
                        "created_at": memory.created_at.isoformat()
                    })
        
        # Sort by similarity and limit
        memory_scores.sort(key=lambda x: x["similarity"], reverse=True)
        return memory_scores[:limit]
    
    async def hybrid_search(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining keyword and semantic search.
        
        Args:
            db: Database session
            user_id: User ID
            query: Search query
            keyword_weight: Weight for keyword matching
            semantic_weight: Weight for semantic matching
            **kwargs: Additional arguments for search
            
        Returns:
            Combined search results
        """
        # Perform semantic search
        semantic_results = await self.semantic_search(db, user_id, query, **kwargs)
        semantic_scores = {r["id"]: r["similarity"] * semantic_weight for r in semantic_results}
        
        # Perform keyword search
        keyword_query = select(Memory).where(
            and_(
                Memory.user_id == user_id,
                func.lower(Memory.content).contains(query.lower())
            )
        )
        
        if kwargs.get("memory_types"):
            keyword_query = keyword_query.where(Memory.memory_type.in_(kwargs["memory_types"]))
        
        if kwargs.get("time_range"):
            keyword_query = keyword_query.where(
                and_(
                    Memory.created_at >= kwargs["time_range"][0],
                    Memory.created_at <= kwargs["time_range"][1]
                )
            )
        
        result = await db.execute(keyword_query.limit(kwargs.get("limit", 20)))
        keyword_memories = result.scalars().all()
        
        # Calculate keyword scores based on match frequency
        keyword_scores = {}
        for memory in keyword_memories:
            match_count = memory.content.lower().count(query.lower())
            normalized_score = min(1.0, match_count / 10.0)  # Normalize to 0-1
            keyword_scores[str(memory.id)] = normalized_score * keyword_weight
        
        # Combine scores
        all_memory_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
        combined_results = []
        
        for memory_id in all_memory_ids:
            combined_score = semantic_scores.get(memory_id, 0) + keyword_scores.get(memory_id, 0)
            
            # Get memory details
            if memory_id in semantic_scores:
                # Already have details from semantic search
                memory_data = next(r for r in semantic_results if r["id"] == memory_id)
                memory_data["combined_score"] = combined_score
                memory_data["search_type"] = "both" if memory_id in keyword_scores else "semantic"
            else:
                # Need to fetch details for keyword-only match
                memory = next(m for m in keyword_memories if str(m.id) == memory_id)
                memory_data = {
                    "memory": memory,
                    "combined_score": combined_score,
                    "search_type": "keyword",
                    "id": str(memory.id),
                    "content": memory.content,
                    "type": memory.memory_type.value,
                    "metadata": memory.meta_data,
                    "created_at": memory.created_at.isoformat()
                }
            
            combined_results.append(memory_data)
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
        return combined_results[:kwargs.get("limit", 20)]
    
    async def get_related_memories(
        self,
        db: AsyncSession,
        memory_id: uuid.UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get memories related to a specific memory.
        
        Args:
            db: Database session
            memory_id: Memory ID to find relations for
            limit: Maximum number of related memories
            
        Returns:
            List of related memories with relationship info
        """
        # Get the memory and its relationships
        memory_result = await db.execute(
            select(Memory).where(Memory.id == memory_id)
        )
        memory = memory_result.scalar_one_or_none()
        
        if not memory:
            return []
        
        # Get relationships
        relations_result = await db.execute(
            select(MemoryRelation)
            .where(
                or_(
                    MemoryRelation.source_memory_id == memory_id,
                    MemoryRelation.target_memory_id == memory_id
                )
            )
            .order_by(MemoryRelation.strength.desc())
            .limit(limit)
        )
        relations = relations_result.scalars().all()
        
        # Get related memories
        related_memories = []
        for relation in relations:
            related_id = (
                relation.target_memory_id 
                if relation.source_memory_id == memory_id 
                else relation.source_memory_id
            )
            
            related_result = await db.execute(
                select(Memory).where(Memory.id == related_id)
            )
            related_memory = related_result.scalar_one_or_none()
            
            if related_memory:
                related_memories.append({
                    "memory": related_memory,
                    "relationship": {
                        "type": relation.relation_type,
                        "strength": relation.strength
                    },
                    "id": str(related_memory.id),
                    "content": related_memory.content,
                    "type": related_memory.memory_type.value,
                    "metadata": related_memory.meta_data,
                    "created_at": related_memory.created_at.isoformat()
                })
        
        return related_memories
    
    async def update_embeddings_batch(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        batch_size: int = 100
    ) -> int:
        """
        Update embeddings for memories that don't have them.
        
        Args:
            db: Database session
            user_id: User ID
            batch_size: Number of memories to process at once
            
        Returns:
            Number of memories updated
        """
        # Find memories without embeddings
        result = await db.execute(
            select(Memory)
            .where(
                and_(
                    Memory.user_id == user_id,
                    Memory.embedding == None
                )
            )
            .limit(batch_size)
        )
        memories = result.scalars().all()
        
        if not memories:
            return 0
        
        # Create embeddings in batch
        contents = [m.content for m in memories]
        embeddings = self.embedding_service.create_batch_embeddings(contents)
        
        # Update memories
        for memory, embedding in zip(memories, embeddings):
            memory.embedding = embedding
        
        await db.commit()
        
        # Update relationships for new embeddings
        for memory in memories:
            await self._update_memory_relationships(db, memory)
        
        return len(memories)
    
    async def _update_memory_relationships(
        self,
        db: AsyncSession,
        memory: Memory,
        similarity_threshold: float = 0.7
    ):
        """
        Update relationships for a memory based on embedding similarity.
        
        Args:
            db: Database session
            memory: Memory to update relationships for
            similarity_threshold: Minimum similarity for creating relationship
        """
        if not memory.embedding:
            return
        
        # Get other memories from the same user
        result = await db.execute(
            select(Memory)
            .where(
                and_(
                    Memory.user_id == memory.user_id,
                    Memory.id != memory.id,
                    Memory.embedding != None
                )
            )
        )
        other_memories = result.scalars().all()
        
        # Find similar memories
        embeddings = [(str(m.id), m.embedding) for m in other_memories]
        relationships = self.embedding_service.update_memory_relationships(
            str(memory.id),
            memory.embedding,
            embeddings,
            similarity_threshold
        )
        
        # Create relationship records
        for related_id, strength in relationships:
            # Check if relationship already exists
            existing = await db.execute(
                select(MemoryRelation)
                .where(
                    or_(
                        and_(
                            MemoryRelation.source_memory_id == memory.id,
                            MemoryRelation.target_memory_id == uuid.UUID(related_id)
                        ),
                        and_(
                            MemoryRelation.source_memory_id == uuid.UUID(related_id),
                            MemoryRelation.target_memory_id == memory.id
                        )
                    )
                )
            )
            
            if not existing.scalar_one_or_none():
                relation = MemoryRelation(
                    source_memory_id=memory.id,
                    target_memory_id=uuid.UUID(related_id),
                    relation_type="similar_content",
                    strength=strength
                )
                db.add(relation)
        
        await db.commit()
    
    async def get_memory_clusters(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        n_clusters: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get memory clusters based on embedding similarity.
        
        Args:
            db: Database session
            user_id: User ID
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary of cluster names to memories
        """
        # Get all memories with embeddings
        result = await db.execute(
            select(Memory)
            .where(
                and_(
                    Memory.user_id == user_id,
                    Memory.embedding != None
                )
            )
        )
        memories = result.scalars().all()
        
        if not memories:
            return {}
        
        # Prepare embeddings for clustering
        embeddings = [(str(m.id), m.embedding) for m in memories]
        
        # Perform clustering
        clusters = self.embedding_service.cluster_embeddings(embeddings, n_clusters)
        
        # Map memories to clusters
        memory_map = {str(m.id): m for m in memories}
        cluster_results = {}
        
        for cluster_id, memory_ids in clusters.items():
            cluster_memories = []
            for mem_id in memory_ids:
                if mem_id in memory_map:
                    memory = memory_map[mem_id]
                    cluster_memories.append({
                        "id": str(memory.id),
                        "content": memory.content,
                        "type": memory.memory_type.value,
                        "metadata": memory.meta_data,
                        "created_at": memory.created_at.isoformat()
                    })
            
            # Generate cluster name based on content
            cluster_name = f"Cluster {cluster_id + 1}"
            if cluster_memories:
                # Use most common words or entities as cluster name
                # This is a simple implementation - could be enhanced
                cluster_name = self._generate_cluster_name(cluster_memories)
            
            cluster_results[cluster_name] = cluster_memories
        
        return cluster_results
    
    def _generate_cluster_name(self, memories: List[Dict[str, Any]]) -> str:
        """Generate a descriptive name for a memory cluster."""
        # Extract common entities or themes
        all_entities = []
        for memory in memories[:5]:  # Sample first 5 memories
            if memory.get("metadata", {}).get("entities"):
                for entity in memory["metadata"]["entities"]:
                    all_entities.append(entity["value"])
        
        if all_entities:
            # Use most common entity
            from collections import Counter
            most_common = Counter(all_entities).most_common(1)
            if most_common:
                return f"{most_common[0][0]} Memories"
        
        # Fallback to memory type
        types = [m["type"] for m in memories]
        if types:
            from collections import Counter
            most_common_type = Counter(types).most_common(1)[0][0]
            return f"{most_common_type.title()} Memories"
        
        return "Memory Cluster"