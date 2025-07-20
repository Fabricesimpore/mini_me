from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.database import get_db
from core.models.user import User
from api.auth import get_current_user
from integrations.todoist.todoist_service import TodoistService
from app.services.memory_service import MemoryService
from app.services.cognitive_profile_service import CognitiveProfileService

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for OAuth states (use Redis in production)
oauth_states = {}


@router.get("/auth")
async def authorize_todoist(
    current_user: dict = Depends(get_current_user)
):
    """Get Todoist OAuth authorization URL"""
    try:
        service = TodoistService()
        
        # Generate state for security
        state = str(uuid.uuid4())
        oauth_states[state] = current_user["user_id"]
        
        auth_url = service.get_authorization_url(state)
        
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error getting auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth-callback")
async def oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth2 callback from Todoist"""
    # Verify state
    user_id = oauth_states.get(state)
    if not user_id:
        return RedirectResponse(
            url="http://localhost:3000/integrations?todoist=error&message=Invalid state",
            status_code=302
        )
    
    # Clean up state
    del oauth_states[state]
    
    try:
        service = TodoistService()
        token_data = service.handle_oauth_callback(code)
        
        # Store tokens in database
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return RedirectResponse(
                url="http://localhost:3000/integrations?todoist=error&message=User not found",
                status_code=302
            )
        
        # Update user's integrations data
        integrations_data = user.integrations_data or {}
        integrations_data['todoist'] = {
            'connected': True,
            'email': token_data['user_email'],
            'access_token': token_data['access_token'],
            'connected_at': datetime.utcnow().isoformat()
        }
        
        await db.execute(
            update(User).where(User.id == user.id).values(
                integrations_data=integrations_data
            )
        )
        await db.commit()
        
        # Store initial memory about Todoist connection
        memory_service = MemoryService()
        await memory_service.store_memory(
            db,
            user_id=user.id,
            memory_type="procedural",
            content=f"Connected Todoist account: {token_data['user_email']}",
            source="todoist_integration",
            metadata={
                "integration": "todoist",
                "action": "connected",
                "email": token_data['user_email']
            }
        )
        
        return RedirectResponse(
            url=f"http://localhost:3000/integrations?todoist=connected&email={token_data['user_email']}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"http://localhost:3000/integrations?todoist=error&message={str(e)}",
            status_code=302
        )


@router.get("/status")
async def get_todoist_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Todoist connection status"""
    user_id = uuid.UUID(current_user["user_id"])
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.integrations_data:
        return {"connected": False}
    
    todoist_data = user.integrations_data.get('todoist', {})
    
    if not todoist_data.get('connected'):
        return {"connected": False}
    
    try:
        # Try to get task stats to verify connection
        service = TodoistService()
        service.set_access_token(todoist_data['access_token'])
        stats = service.get_task_stats()
        
        return {
            "connected": True,
            "email": todoist_data.get('email'),
            "active_tasks": stats['total_active_tasks'],
            "projects": stats['total_projects'],
            "connected_at": todoist_data.get('connected_at')
        }
    except Exception as e:
        logger.error(f"Error checking Todoist status: {str(e)}")
        return {"connected": False, "error": str(e)}


@router.post("/analyze")
async def analyze_tasks(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze task patterns and update cognitive profile"""
    user_id = uuid.UUID(current_user["user_id"])
    
    # Get user's Todoist credentials
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.integrations_data or not user.integrations_data.get('todoist', {}).get('connected'):
        raise HTTPException(status_code=403, detail="Todoist not connected")
    
    try:
        # Analyze tasks
        service = TodoistService()
        service.set_access_token(user.integrations_data['todoist']['access_token'])
        analysis = service.analyze_task_patterns()
        
        # Store insights as memories
        memory_service = MemoryService()
        cognitive_service = CognitiveProfileService()
        
        # Store task management patterns
        await memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="semantic",
            content=f"Task management: {analysis['active_tasks_count']} active tasks across {analysis['projects_count']} projects",
            source="todoist_analysis",
            metadata={
                "analysis_type": "task_overview",
                "stats": {
                    "active_tasks": analysis['active_tasks_count'],
                    "projects": analysis['projects_count'],
                    "completed_30d": analysis['completed_tasks_30d']
                }
            }
        )
        
        # Store productivity insights
        productivity = analysis['productivity_insights']
        if productivity['daily_average'] > 0:
            await memory_service.store_memory(
                db,
                user_id=user_id,
                memory_type="semantic",
                content=f"Completes average of {productivity['daily_average']:.1f} tasks per day, most productive on {productivity.get('most_productive_day', 'weekdays')}",
                source="todoist_analysis",
                metadata={
                    "productivity_metrics": productivity
                }
            )
        
        # Store priority usage patterns
        priority_data = analysis['priority_usage']
        await memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="procedural",
            content=f"Task prioritization: {priority_data['high_priority']} high priority, {priority_data['medium_priority']} medium priority tasks",
            source="todoist_analysis",
            metadata={
                "priority_patterns": priority_data
            }
        )
        
        # Update cognitive profile based on task patterns
        profile_updates = {}
        
        # High conscientiousness if many tasks with due dates and using priorities
        task_patterns = analysis['task_patterns']
        if task_patterns['tasks_with_due_dates_percentage'] > 70:
            profile_updates['conscientiousness'] = 0.8
        elif task_patterns['tasks_with_due_dates_percentage'] > 40:
            profile_updates['conscientiousness'] = 0.6
        
        # Openness based on project diversity
        project_dist = analysis['project_distribution']
        if project_dist['project_count'] > 5:
            profile_updates['openness'] = 0.7
        
        # Update profile if we have insights
        if profile_updates:
            await cognitive_service.update_profile_from_behaviors(
                db, user_id, profile_updates
            )
        
        return {
            "status": "success",
            "tasks_analyzed": analysis['active_tasks_count'],
            "insights": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/summary")
async def get_tasks_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of current tasks"""
    user_id = uuid.UUID(current_user["user_id"])
    
    # Get user's Todoist credentials
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.integrations_data or not user.integrations_data.get('todoist', {}).get('connected'):
        raise HTTPException(status_code=403, detail="Todoist not connected")
    
    try:
        service = TodoistService()
        service.set_access_token(user.integrations_data['todoist']['access_token'])
        
        # Get today's tasks
        today_tasks = service.get_tasks(filter='today')
        overdue_tasks = service.get_tasks(filter='overdue')
        
        # Format tasks for frontend
        def format_task(task):
            return {
                "id": task['id'],
                "content": task['content'],
                "priority": task['priority'],
                "due": task.get('due'),
                "project_id": task.get('project_id'),
                "labels": task.get('labels', [])
            }
        
        return {
            "today": [format_task(t) for t in today_tasks[:10]],
            "overdue": [format_task(t) for t in overdue_tasks[:10]],
            "counts": {
                "today": len(today_tasks),
                "overdue": len(overdue_tasks)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting tasks summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect_todoist(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect Todoist"""
    user_id = uuid.UUID(current_user["user_id"])
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user and user.integrations_data and 'todoist' in user.integrations_data:
        integrations_data = user.integrations_data
        del integrations_data['todoist']
        
        await db.execute(
            update(User).where(User.id == user_id).values(
                integrations_data=integrations_data
            )
        )
        await db.commit()
        
        # Store memory about disconnection
        memory_service = MemoryService()
        await memory_service.store_memory(
            db,
            user_id=user_id,
            memory_type="procedural",
            content="Disconnected Todoist integration",
            source="todoist_integration",
            metadata={
                "integration": "todoist",
                "action": "disconnected"
            }
        )
    
    return {"status": "disconnected"}