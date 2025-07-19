import asyncio
from sqlalchemy import text
from core.database import engine, Base
from core.models.user import User  # Import to register model
from core.models.memory import Memory, MemoryRelation  # Import to register models

async def recreate_memory_tables():
    """Drop and recreate memory tables with correct schema"""
    async with engine.begin() as conn:
        # Drop memory tables
        await conn.execute(text("DROP TABLE IF EXISTS memory_relations CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS memories CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS memorytype CASCADE"))
        print("Memory tables dropped.")
        
        # Create all tables (this will only create missing ones)
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created/updated successfully!")

if __name__ == "__main__":
    asyncio.run(recreate_memory_tables())