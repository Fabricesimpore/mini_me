from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid

router = APIRouter()

# In-memory storage
memories_db = {}

# Schemas
class Memory(BaseModel):
    id: str
    content: str
    category: str
    importance: float  # 0-1
    timestamp: datetime
    tags: List[str]
    source: str  # chat, email, calendar, manual
    context: Optional[str] = None
    related_memories: List[str] = []

class MemoryCreate(BaseModel):
    content: str
    category: str
    importance: float = 0.5
    tags: List[str] = []
    source: str = "manual"
    context: Optional[str] = None

class MemorySearch(BaseModel):
    query: str
    categories: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_importance: Optional[float] = None

# Helper to generate mock memories
def init_mock_memories():
    mock_memories = [
        {
            "id": str(uuid.uuid4()),
            "content": "Learned about FastAPI and async programming patterns",
            "category": "learning",
            "importance": 0.8,
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "tags": ["programming", "python", "fastapi"],
            "source": "manual",
            "context": "During the backend development session"
        },
        {
            "id": str(uuid.uuid4()),
            "content": "Meeting with team about Q4 goals and project timeline",
            "category": "work",
            "importance": 0.9,
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "tags": ["meeting", "planning", "team"],
            "source": "calendar",
            "context": "Quarterly planning session"
        },
        {
            "id": str(uuid.uuid4()),
            "content": "Discovered preference for morning coding sessions",
            "category": "personal",
            "importance": 0.7,
            "timestamp": datetime.utcnow() - timedelta(hours=12),
            "tags": ["productivity", "habits", "self-awareness"],
            "source": "chat",
            "context": "Reflection on productivity patterns"
        }
    ]
    return mock_memories

@router.post("/create", response_model=Memory)
async def create_memory(memory: MemoryCreate):
    """Create a new memory"""
    memory_id = str(uuid.uuid4())
    new_memory = {
        "id": memory_id,
        "content": memory.content,
        "category": memory.category,
        "importance": memory.importance,
        "timestamp": datetime.utcnow(),
        "tags": memory.tags,
        "source": memory.source,
        "context": memory.context,
        "related_memories": []
    }
    
    if "user-1" not in memories_db:
        memories_db["user-1"] = init_mock_memories()
    
    memories_db["user-1"].append(new_memory)
    return Memory(**new_memory)

@router.get("/all", response_model=List[Memory])
async def get_all_memories(
    category: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """Get all memories with optional filtering"""
    if "user-1" not in memories_db:
        memories_db["user-1"] = init_mock_memories()
    
    memories = memories_db["user-1"]
    
    # Filter by category if provided
    if category:
        memories = [m for m in memories if m["category"] == category]
    
    # Sort by timestamp (newest first)
    memories.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Apply pagination
    return [Memory(**m) for m in memories[offset:offset + limit]]

@router.get("/search", response_model=List[Memory])
async def search_memories(
    query: str,
    category: Optional[str] = None,
    min_importance: float = 0.0
):
    """Search memories by content"""
    if "user-1" not in memories_db:
        memories_db["user-1"] = init_mock_memories()
    
    memories = memories_db["user-1"]
    results = []
    
    for memory in memories:
        # Simple text search
        if query.lower() in memory["content"].lower():
            if category and memory["category"] != category:
                continue
            if memory["importance"] < min_importance:
                continue
            results.append(memory)
    
    # Sort by relevance (importance in this case)
    results.sort(key=lambda x: x["importance"], reverse=True)
    
    return [Memory(**m) for m in results]

@router.get("/timeline")
async def get_memory_timeline():
    """Get memories organized by time periods"""
    if "user-1" not in memories_db:
        memories_db["user-1"] = init_mock_memories()
    
    memories = memories_db["user-1"]
    now = datetime.utcnow()
    
    timeline = {
        "today": [],
        "yesterday": [],
        "this_week": [],
        "this_month": [],
        "older": []
    }
    
    for memory in memories:
        time_diff = now - memory["timestamp"]
        
        if time_diff < timedelta(days=1):
            timeline["today"].append(memory)
        elif time_diff < timedelta(days=2):
            timeline["yesterday"].append(memory)
        elif time_diff < timedelta(days=7):
            timeline["this_week"].append(memory)
        elif time_diff < timedelta(days=30):
            timeline["this_month"].append(memory)
        else:
            timeline["older"].append(memory)
    
    # Convert to Memory objects
    for period in timeline:
        timeline[period] = [Memory(**m) for m in timeline[period]]
    
    return timeline

@router.get("/categories")
async def get_memory_categories():
    """Get all memory categories with counts"""
    if "user-1" not in memories_db:
        memories_db["user-1"] = init_mock_memories()
    
    memories = memories_db["user-1"]
    categories = {}
    
    for memory in memories:
        cat = memory["category"]
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    return {
        "categories": categories,
        "total_memories": len(memories)
    }

@router.put("/{memory_id}")
async def update_memory(memory_id: str, importance: float):
    """Update memory importance"""
    if "user-1" not in memories_db:
        return {"error": "No memories found"}
    
    for memory in memories_db["user-1"]:
        if memory["id"] == memory_id:
            memory["importance"] = importance
            return Memory(**memory)
    
    raise HTTPException(status_code=404, detail="Memory not found")

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory"""
    if "user-1" not in memories_db:
        return {"error": "No memories found"}
    
    memories_db["user-1"] = [
        m for m in memories_db["user-1"] 
        if m["id"] != memory_id
    ]
    
    return {"status": "deleted"}