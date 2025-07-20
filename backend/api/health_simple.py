from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Digital Twin Platform",
        "database": "not_checked"  # Skip database check for now
    }