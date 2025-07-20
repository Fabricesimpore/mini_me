"""Gmail OAuth API endpoints"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from typing import Optional
import logging
from ..integrations.gmail.gmail_oauth import gmail_oauth

logger = logging.getLogger(__name__)
router = APIRouter()

def get_current_user():
    # Mock user - in production, get from JWT token
    return "test@example.com"

@router.get("/auth")
async def gmail_auth(user_id: str = Depends(get_current_user)):
    """Get Gmail OAuth URL"""
    try:
        auth_url = gmail_oauth.get_auth_url(user_id)
        return {
            "auth_url": auth_url,
            "message": "Visit the auth_url to connect your Gmail account"
        }
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def gmail_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None)
):
    """Handle Gmail OAuth callback"""
    if error:
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"http://localhost:5173/integrations?gmail=error&message={error}"
        )
    
    try:
        # Handle the OAuth callback
        credentials = gmail_oauth.handle_callback(code, state)
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"http://localhost:5173/integrations?gmail=connected&email={state}"
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"http://localhost:5173/integrations?gmail=error&message=Authentication%20failed"
        )

@router.get("/emails")
async def get_emails(
    query: str = "",
    limit: int = 10,
    user_id: str = Depends(get_current_user)
):
    """Fetch emails from Gmail"""
    try:
        emails = gmail_oauth.fetch_emails(user_id, query, limit)
        return {
            "emails": emails,
            "count": len(emails)
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Gmail")
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis")
async def analyze_emails(user_id: str = Depends(get_current_user)):
    """Analyze email patterns"""
    try:
        analysis = gmail_oauth.analyze_email_patterns(user_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Gmail")
    except Exception as e:
        logger.error(f"Error analyzing emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect")
async def disconnect_gmail(user_id: str = Depends(get_current_user)):
    """Disconnect Gmail"""
    # Remove stored credentials
    if user_id in gmail_oauth.credentials_store:
        del gmail_oauth.credentials_store[user_id]
    
    return {"status": "disconnected", "message": "Gmail disconnected successfully"}