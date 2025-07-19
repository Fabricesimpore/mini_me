import asyncio
import uuid
from sqlalchemy import text
from core.database import engine
from datetime import datetime

async def create_test_user():
    """Create a test user in the database"""
    async with engine.begin() as conn:
        # Create a user with a deterministic UUID based on username
        user_id = uuid.uuid5(uuid.NAMESPACE_DNS, "testuser")
        
        # Check if user exists
        result = await conn.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": "testuser"}
        )
        existing = result.fetchone()
        
        if existing:
            print(f"User 'testuser' already exists with ID: {existing[0]}")
        else:
            # Create user
            await conn.execute(
                text("""
                    INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                    VALUES (:id, :username, :email, :password_hash, :created_at, :updated_at)
                """),
                {
                    "id": user_id,
                    "username": "testuser",
                    "email": "test@example.com",
                    "password_hash": "hashed_password",  # In real app, this would be properly hashed
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
            print(f"Created test user with ID: {user_id}")

if __name__ == "__main__":
    asyncio.run(create_test_user())