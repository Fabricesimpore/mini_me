from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Digital Twin Platform (simplified)...")
    yield
    # Shutdown
    logger.info("Shutting down Digital Twin Platform...")

# Create FastAPI app
app = FastAPI(
    title="Digital Twin Platform",
    description="A platform that creates a true digital twin of you",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import only the essential routers first
try:
    from api import health_simple as health
    app.include_router(health.router, tags=["health"])
    logger.info("Health router loaded")
except Exception as e:
    logger.error(f"Could not load health router: {e}")

try:
    from api import auth_simple as auth
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    logger.info("Auth router loaded")
except Exception as e:
    logger.error(f"Could not load auth router: {e}")

# Load all the new routers
try:
    from api import chat_simple as chat
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    logger.info("Chat router loaded")
except Exception as e:
    logger.error(f"Could not load chat router: {e}")

try:
    from api import behavioral_simple as behavioral
    app.include_router(behavioral.router, prefix="/api/behavioral", tags=["behavioral"])
    logger.info("Behavioral router loaded")
except Exception as e:
    logger.error(f"Could not load behavioral router: {e}")

try:
    from api import memory_simple as memory
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    logger.info("Memory router loaded")
except Exception as e:
    logger.error(f"Could not load memory router: {e}")

try:
    from api import integrations_simple as integrations
    app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
    logger.info("Integrations router loaded")
except Exception as e:
    logger.error(f"Could not load integrations router: {e}")

try:
    from api import ml_simple as ml
    app.include_router(ml.router, prefix="/api/ml", tags=["ml"])
    logger.info("ML router loaded")
except Exception as e:
    logger.error(f"Could not load ml router: {e}")

try:
    from api import recommendations_simple as recommendations
    app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
    logger.info("Recommendations router loaded")
except Exception as e:
    logger.error(f"Could not load recommendations router: {e}")

try:
    from api import gmail_simple as gmail
    app.include_router(gmail.router, prefix="/api/gmail", tags=["gmail"])
    logger.info("Gmail router loaded")
except Exception as e:
    logger.error(f"Could not load gmail router: {e}")

try:
    from api import calendar_simple as calendar
    app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
    logger.info("Calendar router loaded")
except Exception as e:
    logger.error(f"Could not load calendar router: {e}")

try:
    from api import todoist_simple as todoist
    app.include_router(todoist.router, prefix="/api/todoist", tags=["todoist"])
    logger.info("Todoist router loaded")
except Exception as e:
    logger.error(f"Could not load todoist router: {e}")

try:
    from api import outlook_simple as outlook
    app.include_router(outlook.router, prefix="/api/outlook", tags=["outlook"])
    logger.info("Outlook router loaded")
except Exception as e:
    logger.error(f"Could not load outlook router: {e}")

try:
    from api import screen_observer_simple as screen_observer
    app.include_router(screen_observer.router, prefix="/api/screen-observer", tags=["screen_observer"])
    logger.info("Screen Observer router loaded")
except Exception as e:
    logger.error(f"Could not load screen observer router: {e}")

try:
    from api import profile_simple as profile
    app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
    logger.info("Profile router loaded")
except Exception as e:
    logger.error(f"Could not load profile router: {e}")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Digital Twin Platform",
        "status": "operational",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)