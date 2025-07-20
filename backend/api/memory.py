from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from api.auth import get_current_user
from core.models.memory import Memory, MemoryType
from app.services.memory_service import MemoryService

router = APIRouter()
memory_service = MemoryService()


@router.post("/store")
async def store_memory(
    memory_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Store a new memory with embeddings"""
    user_id = current_user["user_id"]
    
    # Validate required fields
    content = memory_data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Memory content is required")
    
    # Parse memory type
    memory_type_str = memory_data.get("type", "episodic")
    try:
        memory_type = MemoryType(memory_type_str)
    except ValueError:
        memory_type = MemoryType.EPISODIC
    
    # Extract metadata
    metadata = memory_data.get("metadata", {})
    confidence_score = memory_data.get("confidence_score", 1.0)
    
    # Create user UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Store memory with embedding
    memory = await memory_service.store_memory(
        db=db,
        user_id=user_uuid,
        content=content,
        memory_type=memory_type,
        metadata=metadata,
        confidence_score=confidence_score
    )
    
    return {
        "status": "memory_stored",
        "memory_id": str(memory.id),
        "type": memory.memory_type.value,
        "has_embedding": bool(memory.embedding),
        "stored_at": memory.created_at.isoformat()
    }


@router.get("/recall")
async def recall_memory(
    query: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 20,
    similarity_threshold: float = 0.5,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Recall memories using semantic search"""
    user_id = current_user["user_id"]
    
    # Create user UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Parse memory types if provided
    memory_types = None
    if memory_type and memory_type != "all":
        try:
            memory_types = [MemoryType(memory_type)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid memory type: {memory_type}")
    
    if not query:
        # If no query, return recent memories
        base_query = select(Memory).where(Memory.user_id == user_uuid)
        if memory_types:
            base_query = base_query.where(Memory.memory_type.in_(memory_types))
        
        result = await db.execute(
            base_query.order_by(Memory.created_at.desc()).limit(limit)
        )
        memories = result.scalars().all()
        
        return {
            "memories": [
                {
                    "id": str(memory.id),
                    "content": memory.content,
                    "type": memory.memory_type.value,
                    "metadata": memory.meta_data,
                    "created_at": memory.created_at.isoformat(),
                    "confidence_score": memory.confidence_score
                }
                for memory in memories
            ],
            "total": len(memories),
            "search_type": "recent"
        }
    
    # Perform semantic search
    results = await memory_service.semantic_search(
        db=db,
        user_id=user_uuid,
        query=query,
        memory_types=memory_types,
        limit=limit,
        similarity_threshold=similarity_threshold
    )
    
    return {
        "memories": results,
        "total": len(results),
        "search_type": "semantic",
        "query": query
    }


@router.get("/related/{memory_id}")
async def get_related_memories(
    memory_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get memories related to a specific memory"""
    try:
        memory_uuid = uuid.UUID(memory_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID")
    
    # Get related memories
    related = await memory_service.get_related_memories(
        db=db,
        memory_id=memory_uuid,
        limit=limit
    )
    
    return {
        "memory_id": memory_id,
        "related_memories": related,
        "total": len(related)
    }


@router.post("/search")
async def hybrid_search(
    search_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform hybrid search combining keyword and semantic search"""
    user_id = current_user["user_id"]
    
    # Extract search parameters
    query = search_data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    memory_type = search_data.get("memory_type")
    keyword_weight = search_data.get("keyword_weight", 0.3)
    semantic_weight = search_data.get("semantic_weight", 0.7)
    limit = search_data.get("limit", 20)
    
    # Create user UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Parse memory types
    memory_types = None
    if memory_type and memory_type != "all":
        try:
            memory_types = [MemoryType(memory_type)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid memory type: {memory_type}")
    
    # Perform hybrid search
    results = await memory_service.hybrid_search(
        db=db,
        user_id=user_uuid,
        query=query,
        keyword_weight=keyword_weight,
        semantic_weight=semantic_weight,
        memory_types=memory_types,
        limit=limit
    )
    
    return {
        "results": results,
        "total": len(results),
        "search_type": "hybrid",
        "query": query,
        "weights": {
            "keyword": keyword_weight,
            "semantic": semantic_weight
        }
    }

@router.post("/update-embeddings")
async def update_embeddings(
    batch_size: int = 100,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update embeddings for memories that don't have them"""
    user_id = current_user["user_id"]
    
    # Create user UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Update embeddings
    updated_count = await memory_service.update_embeddings_batch(
        db=db,
        user_id=user_uuid,
        batch_size=batch_size
    )
    
    return {
        "status": "embeddings_updated",
        "updated_count": updated_count
    }

@router.get("/clusters")
async def get_memory_clusters(
    n_clusters: int = 5,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get memory clusters based on semantic similarity"""
    user_id = current_user["user_id"]
    
    # Create user UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Get clusters
    clusters = await memory_service.get_memory_clusters(
        db=db,
        user_id=user_uuid,
        n_clusters=n_clusters
    )
    
    return {
        "clusters": clusters,
        "n_clusters": n_clusters
    }