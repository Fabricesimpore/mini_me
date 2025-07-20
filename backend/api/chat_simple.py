from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
from jose import JWTError, jwt
import uuid
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Check if OpenAI is available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
    except ImportError:
        OPENAI_AVAILABLE = False
        client = None
else:
    OPENAI_AVAILABLE = False
    client = None

# Import web search capabilities
try:
    from duckduckgo_search import DDGS
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    DDGS = None

# In-memory storage
chat_history = {}
active_connections = {}
knowledge_base = {}  # Store important queries and information

def extract_topics(text: str) -> List[str]:
    """Extract topics from text"""
    # Simple keyword extraction - in production use NLP
    keywords = ['productivity', 'email', 'calendar', 'work', 'meeting', 'task', 
                'project', 'deadline', 'focus', 'break', 'schedule', 'habit']
    
    found_topics = []
    text_lower = text.lower()
    for keyword in keywords:
        if keyword in text_lower:
            found_topics.append(keyword)
    
    return found_topics if found_topics else ['general']

def store_user_query(query: str, response: str, search_results: List[dict] = None):
    """Store user queries and responses for learning"""
    timestamp = datetime.utcnow()
    if 'queries' not in knowledge_base:
        knowledge_base['queries'] = []
    
    entry = {
        'timestamp': timestamp,
        'query': query,
        'response': response,
        'topics': extract_topics(query)
    }
    
    # Store search results if any
    if search_results:
        entry['search_results'] = search_results
        # Also store in a separate searches collection for quick access
        if 'searches' not in knowledge_base:
            knowledge_base['searches'] = []
        knowledge_base['searches'].append({
            'timestamp': timestamp,
            'query': query,
            'results': search_results
        })
    
    knowledge_base['queries'].append(entry)

def perform_web_search(query: str, max_results: int = 3) -> List[dict]:
    """Perform web search using DuckDuckGo"""
    if not WEB_SEARCH_AVAILABLE or not DDGS:
        return []
    
    try:
        ddgs = DDGS()
        results = []
        
        # Search and get top results
        search_results = ddgs.text(query, max_results=max_results)
        
        for result in search_results:
            results.append({
                'title': result.get('title', ''),
                'snippet': result.get('body', ''),
                'url': result.get('link', '')
            })
        
        return results
    except Exception as e:
        print(f"Web search error: {e}")
        return []

def should_search_web(message: str) -> bool:
    """Determine if a message requires web search"""
    search_indicators = [
        'what is', 'who is', 'when is', 'where is', 'how to',
        'latest', 'current', 'news', 'update', 'recent',
        'search', 'find', 'look up', 'google',
        '2024', '2025', 'today', 'yesterday', 'this week'
    ]
    
    message_lower = message.lower()
    return any(indicator in message_lower for indicator in search_indicators)

def generate_ai_response(user_message: str, history: List[dict]) -> str:
    """Generate AI response using OpenAI if available, otherwise use fallback"""
    search_results = []
    
    # Check if we should search the web
    if should_search_web(user_message):
        search_results = perform_web_search(user_message)
    
    if OPENAI_AVAILABLE and client:
        try:
            # Enhanced system prompt with more capabilities
            system_prompt = """You are an advanced Digital Twin AI assistant with the following capabilities:

1. **Personalization**: Learn from the user's communication style, preferences, and patterns
2. **Productivity Optimization**: Help users understand and improve their work habits
3. **Knowledge Integration**: Remember past conversations and build on previous insights
4. **Real-World Awareness**: Provide up-to-date information and practical advice
5. **Pattern Recognition**: Identify trends in user behavior and suggest improvements
6. **Web Search**: When provided with search results, integrate them naturally into your response

Be conversational, insightful, and supportive. Adapt to the user's communication style.
When users ask about current events, technology, or need specific information, provide accurate and helpful responses.
Remember: You're not just a chatbot, you're a digital twin that learns and grows with the user."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent history for context (last 10 messages)
            for msg in history[-10:]:
                if msg.get("content"):
                    role = "user" if not msg.get("is_twin") else "assistant"
                    messages.append({"role": role, "content": msg["content"]})
            
            # Build user message with search results if available
            enhanced_message = user_message
            if search_results:
                enhanced_message += "\n\n[Web Search Results]:\n"
                for i, result in enumerate(search_results, 1):
                    enhanced_message += f"{i}. {result['title']}\n   {result['snippet']}\n   Source: {result['url']}\n\n"
                enhanced_message += "\nPlease incorporate these search results naturally into your response."
            
            # Add current message
            messages.append({"role": "user", "content": enhanced_message})
            
            # Generate response using new API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500,  # Increased for search results
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Store search queries and results
            store_user_query(user_message, ai_response, search_results)
            
            return ai_response
            
        except Exception as e:
            print(f"OpenAI error: {e}")
            # Fall through to use fallback response
    
    # Enhanced fallback responses
    user_lower = user_message.lower()
    
    if any(word in user_lower for word in ["hello", "hi", "hey"]):
        return "Hello! I'm your digital twin assistant. I'm here to help you understand your work patterns and optimize your productivity. What would you like to explore today?"
    
    elif any(word in user_lower for word in ["help", "what can you do"]):
        return "I can help you: 1) Analyze your communication patterns, 2) Track your productivity trends, 3) Understand your work habits, 4) Provide personalized recommendations based on your behavior. What interests you most?"
    
    elif "productive" in user_lower or "productivity" in user_lower:
        return "Productivity is key! Based on your patterns, I notice you tend to be most focused in the mornings. Would you like me to analyze your productivity trends in more detail?"
    
    elif "pattern" in user_lower or "habit" in user_lower:
        return "Understanding your patterns is crucial for optimization. I'm tracking your work habits, communication style, and activity cycles. As we interact more, I'll provide deeper insights into your behavioral patterns."
    
    elif "recommend" in user_lower or "suggestion" in user_lower:
        return "Based on what I know about you so far, I'd recommend scheduling your most important tasks during your peak focus hours (typically 9-11 AM for you). Also, taking short breaks every 90 minutes can help maintain your energy levels."
    
    else:
        return f"I'm processing what you said: '{user_message}'. I'm continuously learning from our conversations to better understand your preferences and work style. The more we interact, the more personalized my insights will become."

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

# Helper function to get user from token
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # For simplicity, return user info from token
    return {"id": email, "email": email}

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
    
    # Generate twin response
    response_content = generate_ai_response(message.content, chat_history.get(user_id, []))
    
    twin_response = {
        "id": str(uuid.uuid4()),
        "content": response_content,
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

@router.get("/knowledge")
async def get_knowledge_base(user = Depends(get_current_user)):
    """Get stored knowledge including searches and learning"""
    return {
        "total_queries": len(knowledge_base.get('queries', [])),
        "total_searches": len(knowledge_base.get('searches', [])),
        "recent_searches": knowledge_base.get('searches', [])[-10:],  # Last 10 searches
        "topics": {
            "most_common": ["productivity", "email", "work", "schedule"],  # Simplified
            "recent": extract_topics(" ".join([q['query'] for q in knowledge_base.get('queries', [])[-5:]]))
        },
        "insights": [
            f"You've made {len(knowledge_base.get('searches', []))} web searches",
            f"Your most common topics are: {', '.join(extract_topics(' '.join([q['query'] for q in knowledge_base.get('queries', [])]))[:3])}",
            "I'm learning from every interaction to better assist you"
        ]
    }

@router.get("/search_history")
async def get_search_history(
    limit: int = 20,
    user = Depends(get_current_user)
):
    """Get user's search history"""
    searches = knowledge_base.get('searches', [])
    
    # Format for frontend display
    formatted_searches = []
    for search in searches[-limit:]:
        formatted_searches.append({
            "timestamp": search['timestamp'].isoformat(),
            "query": search['query'],
            "results_count": len(search.get('results', [])),
            "results": search.get('results', [])[:2]  # Just top 2 results
        })
    
    return {
        "searches": formatted_searches,
        "total": len(searches)
    }