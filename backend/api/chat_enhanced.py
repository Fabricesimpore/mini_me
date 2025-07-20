"""Enhanced chat with OpenAI integration"""
import os
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
import openai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# In-memory storage
chat_history = {}

# Schemas
class ChatMessage(BaseModel):
    content: str
    
class ChatResponse(BaseModel):
    id: str
    content: str
    timestamp: datetime
    user_id: str
    is_twin: bool
    parent_id: Optional[str] = None
    sentiment: Optional[str] = None
    topics: List[str] = []

class ChatWithAI:
    def __init__(self):
        self.system_prompt = """You are a Digital Twin AI assistant that learns from and mirrors the user's communication style, preferences, and patterns. 

Your role is to:
1. Understand the user's personality, work style, and preferences
2. Provide personalized insights about their behavior patterns
3. Help them optimize their productivity and well-being
4. Mirror their communication style while being helpful
5. Remember context from previous conversations

Be conversational, insightful, and supportive. Use the user's past messages to understand their personality and adapt your responses accordingly."""

    def generate_response(self, user_message: str, chat_history_context: List[dict]) -> tuple[str, str, List[str]]:
        """Generate AI response with sentiment and topic analysis"""
        try:
            # Prepare conversation history
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent chat history for context
            for msg in chat_history_context[-10:]:  # Last 10 messages
                role = "user" if not msg.get("is_twin") else "assistant"
                messages.append({"role": role, "content": msg["content"]})
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            
            ai_response = response.choices[0].message.content
            
            # Analyze sentiment
            sentiment_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Classify the sentiment of this message as: positive, negative, neutral, or mixed. Respond with only one word."},
                    {"role": "user", "content": user_message}
                ],
                temperature=0,
                max_tokens=10
            )
            sentiment = sentiment_response.choices[0].message.content.strip().lower()
            
            # Extract topics
            topics_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract 1-3 main topics from this message. Return them as a comma-separated list. Be concise."},
                    {"role": "user", "content": user_message}
                ],
                temperature=0,
                max_tokens=50
            )
            topics = [t.strip() for t in topics_response.choices[0].message.content.split(",")]
            
            return ai_response, sentiment, topics
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to simple response
            return self.fallback_response(user_message), "neutral", ["general"]
    
    def fallback_response(self, user_message: str) -> str:
        """Fallback response when OpenAI is unavailable"""
        responses = {
            "hello": "Hello! I'm your digital twin assistant. How can I help you today?",
            "help": "I can help you understand your work patterns, analyze your productivity, and provide personalized insights.",
            "how are you": "I'm here to help you optimize your day! What would you like to explore?",
        }
        
        user_lower = user_message.lower()
        for key, response in responses.items():
            if key in user_lower:
                return response
        
        return f"I understand you're saying: '{user_message}'. I'm learning your communication patterns to provide better insights. Tell me more about your work style or what you'd like to achieve."

chat_ai = ChatWithAI()

def get_current_user():
    # Mock user authentication
    return "test@example.com"

@router.post("/message", response_model=ChatResponse)
async def send_message(message: ChatMessage, user_id: str = Depends(get_current_user)):
    """Send a message and get AI response"""
    # Store user message
    user_msg_id = str(uuid.uuid4())
    user_msg = {
        "id": user_msg_id,
        "content": message.content,
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "is_twin": False
    }
    
    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append(user_msg)
    
    # Get chat history context
    history_context = chat_history[user_id][-20:]  # Last 20 messages
    
    # Generate AI response
    ai_content, sentiment, topics = chat_ai.generate_response(
        message.content, 
        history_context
    )
    
    # Store AI response
    ai_msg = ChatResponse(
        id=str(uuid.uuid4()),
        content=ai_content,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        is_twin=True,
        parent_id=user_msg_id,
        sentiment=sentiment,
        topics=topics
    )
    
    chat_history[user_id].append(ai_msg.dict())
    
    return ai_msg

@router.get("/history", response_model=List[ChatResponse])
async def get_chat_history(user_id: str = Depends(get_current_user)):
    """Get chat history for the current user"""
    if user_id not in chat_history:
        return []
    
    return [ChatResponse(**msg) for msg in chat_history[user_id]]

@router.get("/insights")
async def get_chat_insights(user_id: str = Depends(get_current_user)):
    """Get insights from chat history"""
    if user_id not in chat_history or not chat_history[user_id]:
        return {"message": "No chat history available for insights"}
    
    messages = chat_history[user_id]
    user_messages = [m for m in messages if not m.get("is_twin")]
    
    # Calculate basic insights
    total_messages = len(user_messages)
    if total_messages == 0:
        return {"message": "No user messages to analyze"}
    
    # Sentiment distribution
    sentiments = [m.get("sentiment", "neutral") for m in messages if m.get("sentiment")]
    sentiment_counts = {s: sentiments.count(s) for s in set(sentiments)}
    
    # Common topics
    all_topics = []
    for m in messages:
        if m.get("topics"):
            all_topics.extend(m["topics"])
    
    topic_counts = {}
    for topic in all_topics:
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    # Sort topics by frequency
    common_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_conversations": total_messages,
        "sentiment_distribution": sentiment_counts,
        "common_topics": [{"topic": t[0], "count": t[1]} for t in common_topics],
        "avg_message_length": sum(len(m["content"]) for m in user_messages) // total_messages,
        "insights": [
            f"You tend to discuss {common_topics[0][0]} frequently" if common_topics else "Keep chatting to build insights",
            f"Your communication style is mostly {max(sentiment_counts, key=sentiment_counts.get)}" if sentiment_counts else "Varied emotional tone",
            "You prefer concise messages" if sum(len(m["content"]) for m in user_messages) // total_messages < 50 else "You enjoy detailed conversations"
        ]
    }

@router.delete("/history/{message_id}")
async def delete_message(message_id: str, user_id: str = Depends(get_current_user)):
    """Delete a specific message"""
    if user_id in chat_history:
        chat_history[user_id] = [m for m in chat_history[user_id] if m["id"] != message_id]
        return {"status": "deleted"}
    return {"status": "not_found"}