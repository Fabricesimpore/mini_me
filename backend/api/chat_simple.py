from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
import asyncio

router = APIRouter()

# In-memory storage
chat_history = {}
active_connections = {}

# Schemas
class ChatMessage(BaseModel):
    content: str
    parent_id: Optional[str] = None

class ChatResponse(BaseModel):
    id: str
    content: str
    timestamp: datetime
    user_id: str
    is_twin: bool
    parent_id: Optional[str] = None

class ChatInsight(BaseModel):
    topic: str
    frequency: int
    sentiment: str
    last_discussed: datetime

# Helper function to get user from token (simplified)
async def get_current_user(token: str) -> dict:
    # In real app, decode JWT token
    return {"id": "user-1", "email": "user@example.com"}

@router.post("/message", response_model=ChatResponse)
async def send_message(message: ChatMessage, user = Depends(get_current_user)):
    """Send a message to the digital twin"""
    user_id = user["id"]
    
    # Initialize chat history for user if not exists
    if user_id not in chat_history:
        chat_history[user_id] = []
    
    # Create user message
    user_msg = {
        "id": str(uuid.uuid4()),
        "content": message.content,
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "is_twin": False,
        "parent_id": message.parent_id
    }
    chat_history[user_id].append(user_msg)
    
    # Generate twin response (simplified)
    twin_response = {
        "id": str(uuid.uuid4()),
        "content": f"I understand you're saying: '{message.content}'. As your digital twin, I'm learning your patterns and will provide more personalized responses as we interact more.",
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "is_twin": True,
        "parent_id": user_msg["id"]
    }
    chat_history[user_id].append(twin_response)
    
    return ChatResponse(**twin_response)

@router.get("/history", response_model=List[ChatResponse])
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    user = Depends(get_current_user)
):
    """Get chat history for the current user"""
    user_id = user["id"]
    
    if user_id not in chat_history:
        return []
    
    messages = chat_history[user_id]
    return [ChatResponse(**msg) for msg in messages[offset:offset + limit]]

@router.get("/insights", response_model=List[ChatInsight])
async def get_chat_insights(user = Depends(get_current_user)):
    """Get insights from chat history"""
    # Mock insights for now
    return [
        ChatInsight(
            topic="Work",
            frequency=15,
            sentiment="positive",
            last_discussed=datetime.utcnow()
        ),
        ChatInsight(
            topic="Health",
            frequency=8,
            sentiment="neutral",
            last_discussed=datetime.utcnow()
        ),
        ChatInsight(
            topic="Learning",
            frequency=12,
            sentiment="positive",
            last_discussed=datetime.utcnow()
        )
    ]

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    active_connections[user_id] = websocket
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message
            response = {
                "type": "message",
                "content": f"Twin response to: {data.get('content', '')}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send response
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        del active_connections[user_id]

@router.delete("/history/{message_id}")
async def delete_message(message_id: str, user = Depends(get_current_user)):
    """Delete a specific message"""
    user_id = user["id"]
    
    if user_id in chat_history:
        chat_history[user_id] = [
            msg for msg in chat_history[user_id] 
            if msg["id"] != message_id
        ]
    
    return {"status": "deleted"}