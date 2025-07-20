"""
Seed test data for Digital Twin Platform
Run this after creating a test user to populate with sample data
"""

import asyncio
import uuid
from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from core.database import get_db, init_db
from core.models.user import User
from core.models.behavioral import BehavioralData
from core.models.memory import Memory
from services.memory_service import MemoryService
from services.cognitive_profile_service import CognitiveProfileService


async def seed_test_data(email: str = "test@example.com"):
    """Seed test data for a user"""
    await init_db()
    
    async for db in get_db():
        # Find user
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found. Please register first.")
            return
        
        print(f"✅ Found user: {user.username}")
        
        # 1. Create Cognitive Profile
        print("\n📊 Creating cognitive profile...")
        cognitive_service = CognitiveProfileService()
        profile_data = {
            "openness": 0.7,
            "conscientiousness": 0.6,
            "extraversion": 0.5,
            "agreeableness": 0.7,
            "neuroticism": 0.3,
            "work_style": "Deep focus with regular breaks",
            "learning_style": "Visual and hands-on learner",
            "decision_style": "analytical",
            "stress_response": "problem_solving",
            "values": ["growth", "creativity", "balance", "authenticity"],
            "interests": ["technology", "psychology", "productivity", "learning"]
        }
        await cognitive_service.create_or_update_profile(db, user.id, profile_data)
        print("✅ Cognitive profile created")
        
        # 2. Add Behavioral Data
        print("\n📈 Adding behavioral data...")
        behaviors = []
        base_time = datetime.utcnow() - timedelta(days=7)
        
        # Simulate a week of browsing patterns
        sites = [
            ("https://github.com/project/repo", "coding"),
            ("https://stackoverflow.com/questions", "learning"),
            ("https://mail.google.com", "communication"),
            ("https://calendar.google.com", "planning"),
            ("https://medium.com/article", "reading"),
            ("https://slack.com", "communication"),
            ("https://localhost:3000", "coding"),
            ("https://news.ycombinator.com", "browsing"),
            ("https://youtube.com/watch", "leisure"),
            ("https://linkedin.com", "networking")
        ]
        
        for day in range(7):
            for hour in [9, 10, 11, 14, 15, 16, 17]:  # Working hours
                for _ in range(random.randint(5, 15)):
                    site, activity = random.choice(sites)
                    behavior = BehavioralData(
                        user_id=user.id,
                        timestamp=base_time + timedelta(days=day, hours=hour, minutes=random.randint(0, 59)),
                        behavior_type="page_visit",
                        source="chrome_extension",
                        data={
                            "url": site,
                            "title": f"Page visit - {activity}",
                            "duration": random.randint(30, 300),
                            "activity_type": activity
                        }
                    )
                    behaviors.append(behavior)
        
        db.add_all(behaviors)
        await db.commit()
        print(f"✅ Added {len(behaviors)} behavioral data points")
        
        # 3. Create Memories
        print("\n🧠 Creating memories...")
        memory_service = MemoryService()
        
        memories = [
            # Episodic memories
            {
                "type": "episodic",
                "content": "Had a productive coding session today. Completed the authentication module for the new project.",
                "emotional_context": "satisfied",
                "tags": ["work", "coding", "achievement"]
            },
            {
                "type": "episodic",
                "content": "Great meeting with the team. We aligned on the project roadmap for Q1.",
                "emotional_context": "motivated",
                "tags": ["work", "meeting", "planning"]
            },
            # Semantic memories
            {
                "type": "semantic",
                "content": "I prefer to start work around 9 AM and have my most productive hours between 10 AM and 12 PM.",
                "tags": ["productivity", "work_patterns", "preferences"]
            },
            {
                "type": "semantic",
                "content": "When making decisions, I like to analyze all options thoroughly before committing.",
                "tags": ["decision_making", "personality", "analytical"]
            },
            # Procedural memories
            {
                "type": "procedural",
                "content": "My morning routine: Coffee first, check emails, review daily tasks, then dive into deep work.",
                "tags": ["routine", "morning", "productivity"]
            },
            {
                "type": "procedural",
                "content": "When stressed, I take a 10-minute walk to clear my mind and gain perspective.",
                "tags": ["stress_management", "wellness", "coping"]
            },
            # Social memories
            {
                "type": "social",
                "content": "Alice is my go-to person for technical discussions. She always provides insightful feedback.",
                "entities": ["Alice Chen"],
                "tags": ["relationships", "work", "collaboration"]
            },
            {
                "type": "social",
                "content": "Weekly sync with Bob helps keep projects on track. He's great at project management.",
                "entities": ["Bob Smith"],
                "tags": ["relationships", "work", "meetings"]
            }
        ]
        
        for memory_data in memories:
            memory_type = memory_data.pop("type")
            await memory_service.store_memory(
                db,
                user_id=user.id,
                memory_type=memory_type,
                content=memory_data["content"],
                source="manual_entry",
                metadata=memory_data,
                tags=memory_data.get("tags", []),
                entities=memory_data.get("entities", []),
                emotional_context=memory_data.get("emotional_context")
            )
        
        print(f"✅ Created {len(memories)} memories")
        
        # 4. Simulate Integration Data
        print("\n🔗 Adding integration data...")
        user.integrations_data = {
            "gmail": {
                "connected": True,
                "email": email,
                "messages_analyzed": 150,
                "writing_style": {
                    "formality": 0.6,
                    "average_length": 120,
                    "response_time_hours": 2.5
                }
            },
            "calendar": {
                "connected": True,
                "email": email,
                "events_analyzed": 200,
                "patterns": {
                    "meeting_hours_per_week": 12,
                    "focus_blocks_per_week": 8,
                    "average_meeting_duration": 45
                }
            }
        }
        
        await db.execute(
            update(User).where(User.id == user.id).values(
                integrations_data=user.integrations_data
            )
        )
        await db.commit()
        print("✅ Added integration data")
        
        print("\n🎉 Test data seeding complete!")
        print(f"\n📋 Summary for user {user.username}:")
        print(f"  - Cognitive profile with personality traits")
        print(f"  - {len(behaviors)} behavioral data points")
        print(f"  - {len(memories)} diverse memories")
        print(f"  - Simulated Gmail and Calendar integrations")
        print("\n🚀 You can now test all features with this rich dataset!")
        
        break  # Exit the async generator


if __name__ == "__main__":
    import sys
    
    email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    print(f"🌱 Seeding test data for user: {email}")
    
    asyncio.run(seed_test_data(email))