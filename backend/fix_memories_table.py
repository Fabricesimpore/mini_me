import asyncio
from sqlalchemy import text
from core.database import engine
from core.models.memory import Memory, MemoryRelation

async def fix_memories_table():
    """Drop and recreate only the memories tables"""
    async with engine.begin() as conn:
        # Drop memory tables in correct order
        await conn.execute(text("DROP TABLE IF EXISTS memory_relations CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS memories CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS memorytype CASCADE"))
        print("Memory tables dropped.")
        
        # Create memory tables
        await conn.run_sync(Memory.metadata.create_all)
        await conn.run_sync(MemoryRelation.metadata.create_all)
        print("Memory tables created successfully!")

if __name__ == "__main__":
    asyncio.run(fix_memories_table())