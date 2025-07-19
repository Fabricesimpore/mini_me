from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import json
import re

from core.database import get_db
from api.auth import get_current_user
from core.models.user import User
from core.models.memory import Memory, MemoryType
from app.services.nlp import NLPService
from app.services.memory import MemoryService

router = APIRouter()

@router.post("/message")
async def send_message(
    message_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a chat message and generate a response"""
    message = message_data.get("message", "")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Initialize services
    nlp_service = NLPService()
    memory_service = MemoryService(db)
    
    # Analyze the message
    analysis = nlp_service.analyze_message(message)
    intent = analysis.get("intent")
    entities = analysis.get("entities", [])
    
    # Process based on intent
    response = ""
    metadata = {
        "intent": intent,
        "entities": entities,
        "memory_stored": False
    }
    
    if intent == "memory_storage":
        # Store the memory
        memory_data = nlp_service.extract_memory_data(message, entities)
        memory = memory_service.store_memory(
            user_id=current_user["user_id"],
            content=message,
            memory_type=memory_data.get("type", MemoryType.EPISODIC),
            meta_data=memory_data.get("metadata", {})
        )
        metadata["memory_stored"] = True
        response = generate_storage_response(memory_data, entities)
    
    elif intent == "memory_query":
        # Query memories
        query_params = nlp_service.extract_query_params(message, entities)
        memories = memory_service.search_memories(
            user_id=current_user["user_id"],
            query=query_params.get("query", message),
            memory_type=query_params.get("type"),
            time_range=query_params.get("time_range")
        )
        response = generate_query_response(memories, query_params)
    
    elif intent == "reflection":
        # Handle self-reflection
        reflection_data = nlp_service.extract_reflection_data(message, entities)
        memory = memory_service.store_memory(
            user_id=current_user["user_id"],
            content=message,
            memory_type=MemoryType.SEMANTIC,
            meta_data={"reflection": True, **reflection_data}
        )
        metadata["memory_stored"] = True
        response = generate_reflection_response(reflection_data)
    
    else:
        # General conversation
        response = generate_conversational_response(message, entities)
    
    # Store the conversation
    conversation_memory = memory_service.store_memory(
        user_id=current_user["user_id"],
        content=json.dumps({
            "user_message": message,
            "assistant_response": response,
            "metadata": metadata
        }),
        memory_type=MemoryType.CONVERSATION,
        meta_data={"timestamp": datetime.utcnow().isoformat()}
    )
    
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
    db: Session = Depends(get_db)
):
    """Get chat history for the current user"""
    memory_service = MemoryService(db)
    
    # Get conversation memories
    conversations = memory_service.get_memories(
        user_id=current_user["user_id"],
        memory_type=MemoryType.CONVERSATION,
        limit=limit
    )
    
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
    
    return {"messages": messages}

def generate_storage_response(memory_data: Dict, entities: List) -> str:
    """Generate a response for memory storage"""
    responses = [
        "I'll remember that for you.",
        "Got it, I've stored that in your memory.",
        "Noted! I'll keep that in mind.",
        "I've saved that information for you."
    ]
    
    # Add specific acknowledgments based on entities
    if any(e["type"] == "person" for e in entities):
        responses.append("I'll remember this about your relationship.")
    if any(e["type"] == "activity" for e in entities):
        responses.append("I've recorded this activity in your timeline.")
    if any(e["type"] == "emotion" for e in entities):
        responses.append("I understand how you're feeling. I've noted this.")
    
    import random
    base_response = random.choice(responses)
    
    # Add context if available
    if memory_data.get("metadata", {}).get("achievement"):
        base_response += " Congratulations on your achievement!"
    elif memory_data.get("metadata", {}).get("emotion") == "stressed":
        base_response += " Is there anything I can help you reflect on?"
    
    return base_response

def generate_query_response(memories: List[Memory], query_params: Dict) -> str:
    """Generate a response for memory queries"""
    if not memories:
        return "I don't have any memories matching that query. Could you provide more details?"
    
    if len(memories) == 1:
        memory = memories[0]
        return f"Based on my records: {memory.content}"
    else:
        response = f"I found {len(memories)} related memories:\n\n"
        for i, memory in enumerate(memories[:5], 1):
            response += f"{i}. {memory.content[:100]}...\n"
        if len(memories) > 5:
            response += f"\n...and {len(memories) - 5} more memories."
        return response

def generate_reflection_response(reflection_data: Dict) -> str:
    """Generate a response for self-reflection"""
    emotion = reflection_data.get("emotion", "")
    
    responses = {
        "stressed": "I understand you're feeling stressed. Taking time to reflect like this is important. What's the main source of stress?",
        "happy": "It's wonderful to hear you're feeling happy! These positive moments are worth remembering.",
        "anxious": "I hear that you're feeling anxious. Would you like to talk more about what's on your mind?",
        "default": "Thank you for sharing your thoughts with me. Self-reflection helps me understand you better."
    }
    
    return responses.get(emotion, responses["default"])

def generate_conversational_response(message: str, entities: List) -> str:
    """Generate a general conversational response"""
    # Simple pattern matching for now
    if "how are you" in message.lower():
        return "I'm here to learn about you and help you remember important moments. How has your day been?"
    elif "thank you" in message.lower():
        return "You're welcome! I'm here whenever you want to talk or need to remember something."
    else:
        return "I'm listening. Feel free to share more about your thoughts, activities, or ask me about your memories."