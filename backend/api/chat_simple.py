from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime
import json
import uuid

from core.database import get_db
from api.auth import get_current_user
from core.models.user import User
from core.models.memory import Memory, MemoryType

router = APIRouter()

# Simple in-memory storage for chat messages (temporary)
chat_history = {}

@router.post("/message")
async def send_message(
    message_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process a chat message and generate a response"""
    message = message_data.get("message", "")
    user_id = current_user["user_id"]
    
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Create a temporary UUID for the user if not valid UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        # Use a deterministic UUID based on username for consistency
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
    
    # Simple intent detection
    intent = "general"
    if any(word in message.lower() for word in ["remember", "went", "did", "had", "met"]):
        intent = "memory_storage"
    elif any(word in message.lower() for word in ["when", "what", "who", "where"]):
        intent = "memory_query"
    elif any(word in message.lower() for word in ["feel", "feeling", "stressed", "happy"]):
        intent = "reflection"
    
    # Generate response based on intent
    if intent == "memory_storage":
        # Store the memory
        memory = Memory(
            user_id=user_uuid,
            content=message,
            memory_type=MemoryType.EPISODIC,
            meta_data={"source": "chat", "intent": intent}
        )
        db.add(memory)
        await db.commit()
        
        response = "I'll remember that for you. Your memory has been stored."
        metadata = {"intent": intent, "memory_stored": True}
    
    elif intent == "memory_query":
        # Query memories
        result = await db.execute(
            select(Memory)
            .where(Memory.user_id == user_uuid)
            .order_by(Memory.created_at.desc())
            .limit(5)
        )
        memories = result.scalars().all()
        
        if memories:
            response = f"I found {len(memories)} recent memories. Your most recent memory: {memories[0].content}"
        else:
            response = "I don't have any memories stored yet. Try telling me about your day!"
        metadata = {"intent": intent, "memories_found": len(memories)}
    
    elif intent == "reflection":
        # Store reflection
        memory = Memory(
            user_id=user_uuid,
            content=message,
            memory_type=MemoryType.SEMANTIC,
            meta_data={"source": "chat", "intent": intent, "reflection": True}
        )
        db.add(memory)
        await db.commit()
        
        response = "Thank you for sharing how you feel. I've noted this in your personal reflections."
        metadata = {"intent": intent, "memory_stored": True}
    
    else:
        response = "I'm here to help you remember and reflect. Tell me about your day, ask about your memories, or share how you're feeling."
        metadata = {"intent": intent}
    
    # Store conversation in memory
    conversation_memory = Memory(
        user_id=user_uuid,
        content=json.dumps({
            "user_message": message,
            "assistant_response": response,
            "metadata": metadata
        }),
        memory_type=MemoryType.CONVERSATION,
        meta_data={"timestamp": datetime.utcnow().isoformat()}
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

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for the current user"""
    user_id = current_user["user_id"]
    
    # Create a temporary UUID for the user if not valid UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        # Use a deterministic UUID based on username for consistency
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