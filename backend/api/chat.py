from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import json
import uuid

from core.database import get_db
from api.auth import get_current_user
from core.models.user import User
from core.models.memory import Memory, MemoryType
from app.services.enhanced_nlp import EnhancedNLPService

router = APIRouter()

@router.post("/message")
async def send_message(
    message_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process a chat message with enhanced NLP"""
    message = message_data.get("message", "")
    user_id = current_user["user_id"]
    
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Create user UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Get last conversation for context
    last_conversation_result = await db.execute(
        select(Memory)
        .where(Memory.user_id == user_uuid)
        .where(Memory.memory_type == MemoryType.CONVERSATION)
        .order_by(Memory.created_at.desc())
        .limit(1)
    )
    last_conversation = last_conversation_result.scalar_one_or_none()
    
    previous_message = None
    previous_response = None
    previous_intent = None
    
    if last_conversation:
        try:
            conv_data = json.loads(last_conversation.content)
            previous_message = conv_data.get("user_message")
            previous_response = conv_data.get("assistant_response")
            previous_metadata = conv_data.get("metadata", {})
            previous_intent = previous_metadata.get("intent")
        except:
            pass
    
    # Initialize enhanced NLP service
    nlp = EnhancedNLPService()
    
    # Check if we're in an active conversation (last message within 5 minutes)
    in_conversation = False
    if last_conversation:
        time_diff = datetime.utcnow() - last_conversation.created_at
        in_conversation = time_diff.total_seconds() < 300  # 5 minutes
    
    # Analyze message with context
    analysis = nlp.analyze_message(message, previous_response, previous_intent)
    intent = analysis["intent"]
    confidence = analysis["confidence"]
    entities = analysis["entities"]
    time_info = analysis["time_info"]
    
    # Process based on intent
    response = ""
    metadata = {
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
        "time_info": time_info,
        "memory_stored": False
    }
    
    if intent == "memory_storage":
        # Store the memory with extracted metadata
        # Convert date objects to strings for JSON serialization
        serializable_time_info = time_info.copy()
        if serializable_time_info.get("date"):
            if hasattr(serializable_time_info["date"], "isoformat"):
                serializable_time_info["date"] = serializable_time_info["date"].isoformat()
        
        memory_metadata = {
            "source": "chat",
            "intent": intent,
            "entities": entities,
            "time_info": serializable_time_info
        }
        
        # Add extracted entities to metadata
        for entity in entities:
            if entity["type"] not in memory_metadata:
                memory_metadata[entity["type"]] = []
            memory_metadata[entity["type"]].append(entity["value"])
        
        memory = Memory(
            user_id=user_uuid,
            content=message,
            memory_type=MemoryType.EPISODIC,
            meta_data=memory_metadata
        )
        db.add(memory)
        await db.commit()
        
        metadata["memory_stored"] = True
        response = nlp.generate_contextual_response(intent, entities, message=message, 
                                                   previous_message=previous_response, 
                                                   in_conversation=in_conversation)
    
    elif intent == "memory_query":
        # Build query based on time info and entities
        query = select(Memory).where(Memory.user_id == user_uuid)
        
        # Apply time filters if present
        if time_info["has_time"] and time_info["date"]:
            target_date = time_info["date"]
            if isinstance(target_date, date):
                # Query for the entire day
                start_of_day = datetime.combine(target_date, datetime.min.time())
                end_of_day = datetime.combine(target_date, datetime.max.time())
                query = query.where(
                    and_(
                        Memory.created_at >= start_of_day,
                        Memory.created_at <= end_of_day
                    )
                )
        
        # Search for entity mentions in content
        search_terms = []
        for entity in entities:
            if entity["type"] in ["person", "place", "activity"]:
                search_terms.append(entity["value"].lower())
        
        if search_terms:
            search_conditions = []
            for term in search_terms:
                search_conditions.append(func.lower(Memory.content).contains(term))
            
            query = query.where(or_(*search_conditions))
        
        # Execute query
        result = await db.execute(
            query.order_by(Memory.created_at.desc()).limit(10)
        )
        memories = result.scalars().all()
        
        response = nlp.generate_contextual_response(intent, entities, memories, time_info, message, 
                                                   previous_response, in_conversation)
        metadata["memories_found"] = len(memories)
    
    elif intent == "reflection":
        # Store as semantic memory
        memory = Memory(
            user_id=user_uuid,
            content=message,
            memory_type=MemoryType.SEMANTIC,
            meta_data={
                "source": "chat",
                "intent": intent,
                "reflection": True,
                "entities": entities,
                "emotions": [e["value"] for e in entities if e["type"] == "emotion"]
            }
        )
        db.add(memory)
        await db.commit()
        
        metadata["memory_stored"] = True
        response = nlp.generate_contextual_response(intent, entities, message=message, 
                                                   previous_message=previous_response, 
                                                   in_conversation=in_conversation)
    
    elif intent == "planning":
        # Store as procedural memory for future tasks
        # Convert date objects to strings for JSON serialization
        serializable_time_info = time_info.copy()
        if serializable_time_info.get("date"):
            if hasattr(serializable_time_info["date"], "isoformat"):
                serializable_time_info["date"] = serializable_time_info["date"].isoformat()
        
        memory = Memory(
            user_id=user_uuid,
            content=message,
            memory_type=MemoryType.PROCEDURAL,
            meta_data={
                "source": "chat",
                "intent": intent,
                "future_task": True,
                "entities": entities,
                "time_info": serializable_time_info
            }
        )
        db.add(memory)
        await db.commit()
        
        metadata["memory_stored"] = True
        response = nlp.generate_contextual_response(intent, entities, message=message, 
                                                   previous_message=previous_response, 
                                                   in_conversation=in_conversation)
    
    else:
        # General conversation - still store but with lower importance
        response = nlp.generate_contextual_response(intent, entities, message=message, 
                                                   previous_message=previous_response, 
                                                   in_conversation=in_conversation)
    
    # Always store the conversation
    # Create serializable metadata
    serializable_metadata = metadata.copy()
    if serializable_metadata.get("time_info") and serializable_metadata["time_info"].get("date"):
        if hasattr(serializable_metadata["time_info"]["date"], "isoformat"):
            serializable_metadata["time_info"]["date"] = serializable_metadata["time_info"]["date"].isoformat()
    
    conversation_memory = Memory(
        user_id=user_uuid,
        content=json.dumps({
            "user_message": message,
            "assistant_response": response,
            "metadata": serializable_metadata
        }),
        memory_type=MemoryType.CONVERSATION,
        meta_data={
            "timestamp": datetime.utcnow().isoformat(),
            "intent": intent,
            "confidence": confidence
        }
    )
    db.add(conversation_memory)
    await db.commit()
    await db.refresh(conversation_memory)
    
    return {
        "id": str(conversation_memory.id),
        "response": response,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": metadata
    }

@router.get("/search")
async def search_memories(
    query: str,
    memory_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Advanced memory search with filters"""
    user_id = current_user["user_id"]
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Build query
    search_query = select(Memory).where(Memory.user_id == user_uuid)
    
    # Filter by memory type
    if memory_type and memory_type != "all":
        try:
            mem_type = MemoryType(memory_type)
            search_query = search_query.where(Memory.memory_type == mem_type)
        except ValueError:
            pass
    
    # Filter by date range
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            search_query = search_query.where(Memory.created_at >= start_dt)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            search_query = search_query.where(Memory.created_at <= end_dt)
        except:
            pass
    
    # Text search
    if query:
        search_query = search_query.where(
            func.lower(Memory.content).contains(query.lower())
        )
    
    # Execute search
    result = await db.execute(
        search_query.order_by(Memory.created_at.desc()).limit(limit)
    )
    memories = result.scalars().all()
    
    # Format results
    return {
        "results": [
            {
                "id": str(memory.id),
                "content": memory.content,
                "type": memory.memory_type.value,
                "metadata": memory.meta_data,
                "created_at": memory.created_at.isoformat()
            }
            for memory in memories
        ],
        "count": len(memories),
        "query": query,
        "filters": {
            "memory_type": memory_type,
            "start_date": start_date,
            "end_date": end_date
        }
    }

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history with enhanced metadata"""
    user_id = current_user["user_id"]
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Get conversation memories
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == user_uuid)
        .where(Memory.memory_type == MemoryType.CONVERSATION)
        .order_by(Memory.created_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()
    
    messages = []
    for conv in conversations:
        try:
            data = json.loads(conv.content)
            # Add user message
            messages.append({
                "id": f"{conv.id}_user",
                "content": data.get("user_message", ""),
                "role": "user",
                "timestamp": conv.created_at.isoformat()
            })
            # Add assistant response
            messages.append({
                "id": f"{conv.id}_assistant",
                "content": data.get("assistant_response", ""),
                "role": "assistant",
                "timestamp": conv.created_at.isoformat(),
                "metadata": data.get("metadata", {})
            })
        except:
            continue
    
    # Reverse to get chronological order
    messages.reverse()
    
    return {"messages": messages}

@router.get("/insights")
async def get_memory_insights(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get insights from user's memories"""
    user_id = current_user["user_id"]
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Get recent memories
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == user_uuid)
        .where(Memory.created_at >= datetime.utcnow() - timedelta(days=30))
        .order_by(Memory.created_at.desc())
    )
    recent_memories = result.scalars().all()
    
    # Analyze patterns
    insights = {
        "total_memories": len(recent_memories),
        "memory_types": {},
        "common_activities": {},
        "frequent_people": {},
        "emotional_patterns": {},
        "active_times": {}
    }
    
    for memory in recent_memories:
        # Count by type
        mem_type = memory.memory_type.value
        insights["memory_types"][mem_type] = insights["memory_types"].get(mem_type, 0) + 1
        
        # Extract patterns from metadata
        if memory.meta_data:
            # Activities
            activities = memory.meta_data.get("activity", [])
            if isinstance(activities, list):
                for activity in activities:
                    insights["common_activities"][activity] = insights["common_activities"].get(activity, 0) + 1
            
            # People
            people = memory.meta_data.get("person", [])
            if isinstance(people, list):
                for person in people:
                    insights["frequent_people"][person] = insights["frequent_people"].get(person, 0) + 1
            
            # Emotions
            emotions = memory.meta_data.get("emotions", [])
            if isinstance(emotions, list):
                for emotion in emotions:
                    insights["emotional_patterns"][emotion] = insights["emotional_patterns"].get(emotion, 0) + 1
        
        # Time patterns
        hour = memory.created_at.hour
        time_period = "morning" if 6 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening" if 18 <= hour < 22 else "night"
        insights["active_times"][time_period] = insights["active_times"].get(time_period, 0) + 1
    
    # Sort and limit results
    insights["common_activities"] = dict(sorted(insights["common_activities"].items(), key=lambda x: x[1], reverse=True)[:10])
    insights["frequent_people"] = dict(sorted(insights["frequent_people"].items(), key=lambda x: x[1], reverse=True)[:10])
    insights["emotional_patterns"] = dict(sorted(insights["emotional_patterns"].items(), key=lambda x: x[1], reverse=True)[:10])
    
    return insights