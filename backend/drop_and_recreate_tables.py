import asyncio
from core.database import engine, Base
from core.models.user import User
from core.models.memory import Memory, MemoryRelation

async def recreate_tables():
    """Drop and recreate all database tables"""
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        print("All tables dropped.")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(recreate_tables())