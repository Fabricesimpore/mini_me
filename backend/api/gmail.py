from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import uuid
import os

from core.database import get_db
from api.auth import get_current_user
from integrations.gmail.gmail_service import GmailService
from app.services.memory_service import MemoryService
from core.models.memory import MemoryType

router = APIRouter()
memory_service = MemoryService()

# Store temporary OAuth states
oauth_states = {}

@router.get("/auth")
async def gmail_auth(
    current_user: dict = Depends(get_current_user),
    redirect_uri: str = "http://localhost:8000/api/gmail/callback"
):
    """Initiate Gmail OAuth2 authentication"""
    user_id = current_user["user_id"]
    
    # Create Gmail service
    gmail_service = GmailService(user_id)
    
    # Get auth URL
    auth_url = gmail_service.get_auth_url(redirect_uri)
    
    # Store state for callback
    oauth_states[user_id] = {
        "redirect_uri": redirect_uri,
        "timestamp": datetime.utcnow()
    }
    
    return {
        "auth_url": auth_url,
        "message": "Please visit the auth_url to grant permissions"
    }

@router.get("/callback")
async def gmail_callback(
    code: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle Gmail OAuth2 callback"""
    # In production, you'd validate the state parameter
    # For now, we'll use the most recent auth request
    
    if not oauth_states:
        raise HTTPException(status_code=400, detail="No pending auth request")
    
    # Get the most recent auth request
    user_id = list(oauth_states.keys())[-1]
    auth_data = oauth_states.pop(user_id)
    
    # Create Gmail service
    gmail_service = GmailService(user_id)
    
    try:
        # Handle callback
        result = gmail_service.handle_oauth_callback(code, auth_data["redirect_uri"])
        
        # Store connection info as memory
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
        
        await memory_service.store_memory(
            db=db,
            user_id=user_uuid,
            content=f"Connected Gmail account: {result['email']}",
            memory_type=MemoryType.PROCEDURAL,
            metadata={
                "integration": "gmail",
                "email": result["email"],
                "connected_at": datetime.utcnow().isoformat()
            }
        )
        
        # Redirect to frontend with success
        return RedirectResponse(url=f"http://localhost:3000/integrations?gmail=connected&email={result['email']}")
        
    except Exception as e:
        # Redirect with error
        return RedirectResponse(url=f"http://localhost:3000/integrations?gmail=error&message={str(e)}")

@router.post("/analyze")
async def analyze_emails(
    max_emails: int = 100,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze user's sent emails for communication patterns"""
    user_id = current_user["user_id"]
    
    # Create Gmail service
    gmail_service = GmailService(user_id)
    
    try:
        # Analyze emails
        analysis = gmail_service.analyze_sent_emails(max_emails)
        
        # Store insights as memories
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
        
        # Store communication style
        if analysis.get("writing_style"):
            style_content = f"Email writing style: "
            if analysis["writing_style"].get("preferred_greeting"):
                style_content += f"Usually greet with '{analysis['writing_style']['preferred_greeting']}'. "
            if analysis["writing_style"].get("preferred_closing"):
                style_content += f"Usually close with '{analysis['writing_style']['preferred_closing']}'. "
            if analysis["writing_style"].get("avg_word_count"):
                style_content += f"Average email length is {int(analysis['writing_style']['avg_word_count'])} words."
            
            await memory_service.store_memory(
                db=db,
                user_id=user_uuid,
                content=style_content,
                memory_type=MemoryType.PROCEDURAL,
                metadata={
                    "source": "gmail_analysis",
                    "type": "communication_style",
                    "analysis": analysis["writing_style"]
                }
            )
        
        # Store top contacts as social memories
        if analysis.get("top_contacts"):
            for email, data in analysis["top_contacts"][:5]:
                await memory_service.store_memory(
                    db=db,
                    user_id=user_uuid,
                    content=f"Frequently email with {email} ({data['count']} times)",
                    memory_type=MemoryType.SOCIAL,
                    metadata={
                        "source": "gmail_analysis",
                        "person": email,
                        "relationship_type": data["type"],
                        "frequency": data["count"]
                    }
                )
        
        return {
            "status": "success",
            "emails_analyzed": analysis["total_analyzed"],
            "insights": {
                "writing_style": analysis.get("writing_style", {}),
                "top_contacts": analysis.get("top_contacts", [])[:5],
                "communication_patterns": analysis.get("communication_patterns", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_email_templates(
    current_user: dict = Depends(get_current_user)
):
    """Get common email templates based on user's writing patterns"""
    user_id = current_user["user_id"]
    
    # Create Gmail service
    gmail_service = GmailService(user_id)
    
    try:
        templates = gmail_service.get_email_templates()
        
        return {
            "templates": templates,
            "total": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/draft")
async def create_draft(
    draft_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an email draft using learned patterns"""
    user_id = current_user["user_id"]
    
    # Validate input
    to_email = draft_data.get("to")
    subject = draft_data.get("subject")
    body = draft_data.get("body")
    
    if not all([to_email, subject, body]):
        raise HTTPException(status_code=400, detail="Missing required fields: to, subject, body")
    
    # Create Gmail service
    gmail_service = GmailService(user_id)
    
    try:
        # Get user's writing style from memory
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
        
        # Search for communication style memories
        style_memories = await memory_service.semantic_search(
            db=db,
            user_id=user_uuid,
            query="email writing style greeting closing",
            memory_types=[MemoryType.PROCEDURAL],
            limit=1
        )
        
        # Apply learned style to draft
        if style_memories:
            style_data = style_memories[0].get("metadata", {}).get("analysis", {})
            
            # Add greeting if not present
            if style_data.get("preferred_greeting") and not any(g in body.lower()[:20] for g in ["hi", "hello", "dear", "hey"]):
                greeting = style_data["preferred_greeting"].capitalize()
                body = f"{greeting},\n\n{body}"
            
            # Add closing if not present
            if style_data.get("preferred_closing") and not any(c in body.lower()[-50:] for c in ["regards", "best", "sincerely", "thanks"]):
                closing = style_data["preferred_closing"].capitalize()
                body = f"{body}\n\n{closing},"
        
        # Create draft
        result = gmail_service.draft_email(to_email, subject, body)
        
        # Store as memory
        await memory_service.store_memory(
            db=db,
            user_id=user_uuid,
            content=f"Drafted email to {to_email} with subject: {subject}",
            memory_type=MemoryType.PROCEDURAL,
            metadata={
                "source": "gmail_draft",
                "to": to_email,
                "subject": subject,
                "draft_id": result.get("draft_id")
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating draft: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_gmail_status(
    current_user: dict = Depends(get_current_user)
):
    """Check Gmail integration status"""
    user_id = current_user["user_id"]
    
    # Check if credentials exist
    credentials_path = f"credentials/gmail_{user_id}_token.json"
    is_connected = os.path.exists(credentials_path)
    
    profile = {}
    if is_connected:
        try:
            gmail_service = GmailService(user_id)
            gmail_service._initialize_service()
            profile = gmail_service._get_user_profile()
        except Exception as e:
            is_connected = False
            logger.error(f"Error checking Gmail status: {e}")
    
    return {
        "connected": is_connected,
        "email": profile.get("emailAddress") if profile else None,
        "messages_total": profile.get("messagesTotal") if profile else None,
        "threads_total": profile.get("threadsTotal") if profile else None
    }

# Import datetime at the top of the file
from datetime import datetime
import logging

logger = logging.getLogger(__name__)