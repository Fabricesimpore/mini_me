import asyncio
import uuid
from sqlalchemy import text
from core.database import engine
from datetime import datetime

async def create_all_users():
    """Create all necessary users in the database"""
    async with engine.begin() as conn:
        # List of usernames that might be used
        usernames = ["testuser", "admin", "user", "demo"]
        
        # Also create the specific UUID that was seen in the error
        specific_users = [
            {"id": uuid.UUID("d92b97a9-9500-58b0-a68f-feb711bc66f5"), "username": "frontend_user"},
            {"id": uuid.UUID("cec85b2b-ae3e-5a75-82f3-15997f21a8fc"), "username": "testuser"}
        ]
        
        # Create users with deterministic UUIDs
        for username in usernames:
            user_id = uuid.uuid5(uuid.NAMESPACE_DNS, username)
            
            # Check if user exists
            result = await conn.execute(
                text("SELECT id FROM users WHERE username = :username OR id = :id"),
                {"username": username, "id": user_id}
            )
            existing = result.fetchone()
            
            if not existing:
                await conn.execute(
                    text("""
                        INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                        VALUES (:id, :username, :email, :password_hash, :created_at, :updated_at)
                    """),
                    {
                        "id": user_id,
                        "username": username,
                        "email": f"{username}@example.com",
                        "password_hash": "hashed_password",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                )
                print(f"Created user '{username}' with ID: {user_id}")
            else:
                print(f"User '{username}' already exists")
        
        # Create specific users seen in errors
        for user_data in specific_users:
            result = await conn.execute(
                text("SELECT id FROM users WHERE id = :id"),
                {"id": user_data["id"]}
            )
            existing = result.fetchone()
            
            if not existing:
                await conn.execute(
                    text("""
                        INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                        VALUES (:id, :username, :email, :password_hash, :created_at, :updated_at)
                    """),
                    {
                        "id": user_data["id"],
                        "username": user_data["username"],
                        "email": f"{user_data['username']}@example.com",
                        "password_hash": "hashed_password",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                )
                print(f"Created user '{user_data['username']}' with specific ID: {user_data['id']}")

if __name__ == "__main__":
    asyncio.run(create_all_users())