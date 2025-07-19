import asyncio
from core.database import engine, Base
from core.models.user import User
from core.models.memory import Memory, MemoryRelation

async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        await conn.run_sync(Base.metadata.create_all)
        print("All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())